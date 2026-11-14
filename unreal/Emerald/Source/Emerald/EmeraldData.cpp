#include "EmeraldData.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/FileManager.h"

const FEmeraldCell* FEmeraldMap::Cell(FIntPoint Tile) const
{
    if (Tile.X < 0 || Tile.Y < 0 || Tile.X >= Width || Tile.Y >= Height) return nullptr;
    return Cells.IsValidIndex(Tile.Y*Width+Tile.X) ? &Cells[Tile.Y*Width+Tile.X] : nullptr;
}

void UEmeraldData::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    FString Error;
    if (!Load(FPaths::ProjectContentDir()/TEXT("Imported/Data/littleroot.json"), Error))
    {
        UE_LOG(LogTemp, Error, TEXT("EMERALD_DATA load failed: %s"), *Error);
        if(FParse::Param(FCommandLine::Get(),TEXT("EmeraldSmoke"))) FinishSmoke(false,Error);
        return;
    }
    bEventSmoke=FParse::Param(FCommandLine::Get(),TEXT("EmeraldEventSmoke"));
    FParse::Value(FCommandLine::Get(),TEXT("EmeraldEventShotDir="),EventShotDirectory);
    Story=MakeUnique<FEmeraldEventRuntime>();
    if(!Story->Load(FPaths::ProjectContentDir()/TEXT("Imported/Data/source-events.json"),Root,Error))
    { UE_LOG(LogTemp,Error,TEXT("EMERALD_SOURCE load failed: %s"),*Error); Story.Reset(); }
    else
    {
        Story->Reset(FParse::Param(FCommandLine::Get(),TEXT("EmeraldFemale"))?1:0,true);
        Story->Enabled=!FParse::Param(FCommandLine::Get(),TEXT("EmeraldSmoke")) && (!FParse::Value(FCommandLine::Get(),TEXT("EmeraldCaptureDir="),CaptureDirectory) || FParse::Param(FCommandLine::Get(),TEXT("EmeraldCaptureCharacters")));
    }
    if(FParse::Value(FCommandLine::Get(),TEXT("EmeraldCaptureDir="),CaptureDirectory))
    {
        IFileManager::Get().MakeDirectory(*CaptureDirectory,true);
        for(const auto& Value:Root->GetArrayField(TEXT("maps"))) CaptureMapIds.Add(Value->AsObject()->GetStringField(TEXT("id")));
        bCaptureSweep=true;
    }
    if(FParse::Param(FCommandLine::Get(),TEXT("EmeraldSmoke")))
    {
        FString PlanText;
        TSharedPtr<FJsonObject> Plan;
        if(!FFileHelper::LoadFileToString(PlanText,*(FPaths::ProjectContentDir()/TEXT("Imported/Data/traversal.json"))) ||
           !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(PlanText),Plan) || !Plan.IsValid() ||
           Plan->GetStringField(TEXT("schema"))!=TEXT("emerald.traversal/1") ||
           Plan->GetStringField(TEXT("source_revision"))!=Root->GetStringField(TEXT("source_revision")))
        { FinishSmoke(false,TEXT("Missing, invalid or stale input traversal plan")); return; }
        SmokeSteps=Plan->GetArrayField(TEXT("steps"));
        if(SmokeSteps.IsEmpty() || Plan->GetArrayField(TEXT("covered_warps")).Num()!=13)
        { FinishSmoke(false,TEXT("Incomplete warp scenario")); return; }
        bSmokeActive=true;
        UE_LOG(LogTemp,Display,TEXT("EMERALD_SMOKE armed %d input steps"),SmokeSteps.Num());
    }
}

bool UEmeraldData::Load(const FString& Path, FString& Error)
{
    FString Text;
    Maps.Empty(); Root.Reset();
    if (!FFileHelper::LoadFileToString(Text, *Path)) { Error = TEXT("Missing generated manifest; run tools/import_littleroot.py"); return false; }
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Root) || !Root.IsValid())
    { Error = TEXT("Invalid manifest JSON"); return false; }
    FString Schema;
    const TArray<TSharedPtr<FJsonValue>>* Rows;
    if (!Root->TryGetStringField(TEXT("schema"), Schema) || Schema != TEXT("emerald.littleroot/1") || !Root->TryGetArrayField(TEXT("maps"), Rows))
    { Error = TEXT("Unsupported manifest schema"); return false; }
    for (const auto& Row : *Rows)
    {
        const auto O = Row->AsObject();
        if (!O.IsValid()) { Error = TEXT("Invalid map record"); return false; }
        FEmeraldMap M;
        const TSharedPtr<FJsonObject>* G;
        if (!O->TryGetStringField(TEXT("id"), M.Id) || !O->TryGetStringField(TEXT("name"), M.Name) || !O->TryGetObjectField(TEXT("geometry"), G))
        { Error = TEXT("Missing map identity/geometry"); return false; }
        if (Maps.Contains(M.Id)) { Error = TEXT("Duplicate map ID"); return false; }
        M.Source = O;
        if (!(*G)->TryGetNumberField(TEXT("width"), M.Width) || !(*G)->TryGetNumberField(TEXT("height"), M.Height) || M.Width < 1 || M.Height < 1 || M.Width > 256 || M.Height > 256)
        { Error = TEXT("Invalid dimensions"); return false; }
        const TArray<TSharedPtr<FJsonValue>>* Cells;
        if (!(*G)->TryGetArrayField(TEXT("cells"), Cells) || Cells->Num() != M.Width*M.Height)
        { Error = TEXT("Cell count differs from map dimensions"); return false; }
        for (int32 I = 0; I < Cells->Num(); ++I)
        {
            const auto C = (*Cells)[I]->AsObject();
            int32 Packed, X, Y, Meta, Collision, Elevation, Behavior;
            if (!C.IsValid() || !C->TryGetNumberField(TEXT("source_word"),Packed) || Packed < 0 || Packed > 65535 ||
                !C->TryGetNumberField(TEXT("x"),X) || !C->TryGetNumberField(TEXT("y"),Y) || X != I%M.Width || Y != I/M.Width ||
                !C->TryGetNumberField(TEXT("metatile_id"),Meta) || !C->TryGetNumberField(TEXT("collision"),Collision) ||
                !C->TryGetNumberField(TEXT("elevation"),Elevation) || !C->TryGetNumberField(TEXT("behavior"),Behavior) ||
                Meta != (Packed&1023) || Collision != ((Packed>>10)&3) || Elevation != (Packed>>12))
            { Error = TEXT("Corrupt or reordered cell"); return false; }
            M.Cells.Add({static_cast<uint16>(Packed), Meta, Collision, Elevation, Behavior});
        }
        const TArray<TSharedPtr<FJsonValue>>* Warps;
        if (!O->TryGetArrayField(TEXT("warp_events"), Warps)) { Error = TEXT("Missing warp array"); return false; }
        for (const auto& Value : *Warps)
        {
            const auto W = Value->AsObject();
            FEmeraldWarp Warp;
            FString Index;
            if (!W.IsValid() || !W->TryGetNumberField(TEXT("x"),Warp.Tile.X) || !W->TryGetNumberField(TEXT("y"),Warp.Tile.Y) ||
                !W->TryGetStringField(TEXT("dest_map"),Warp.Destination) || !W->TryGetStringField(TEXT("dest_warp_id"),Index) || !Index.IsNumeric())
            { Error = TEXT("Invalid warp"); return false; }
            Warp.DestinationIndex = FCString::Atoi(*Index);
            if (!M.Cell(Warp.Tile)) { Error = TEXT("Warp outside map"); return false; }
            M.Warps.Add(Warp);
        }
        Maps.Add(M.Id, MoveTemp(M));
    }
    if (Maps.Num() != 6) { Error = TEXT("Expected the exterior plus all five interiors"); Maps.Empty(); return false; }
    for (const auto& Pair : Maps)
        for (const auto& W : Pair.Value.Warps)
        {
            const auto* D = Map(W.Destination);
            if (!D || !D->Warps.IsValidIndex(W.DestinationIndex))
            { Error = TEXT("Unresolved warp destination"); Maps.Empty(); return false; }
        }
    UE_LOG(LogTemp, Display, TEXT("EMERALD_DATA loaded %d maps, source %s"), Maps.Num(), *Root->GetStringField(TEXT("source_revision")));
    return true;
}

bool UEmeraldData::ResolveWarp(const FString& MapId, int32 Index, FString& TargetMap, FIntPoint& TargetTile) const
{
    const auto* M = Map(MapId);
    if (!M || !M->Warps.IsValidIndex(Index)) return false;
    const auto& W = M->Warps[Index];
    const auto* D = Map(W.Destination);
    if (!D || !D->Warps.IsValidIndex(W.DestinationIndex)) return false;
    TargetMap = D->Id;
    TargetTile = D->Warps[W.DestinationIndex].Tile;
    return true;
}

bool UEmeraldData::CanEnter(const FString& MapId, FIntPoint Tile, int32 FromElevation) const
{
    const auto* M = Map(MapId);
    const auto* C = M ? M->Cell(Tile) : nullptr;
    return C && C->Collision == 0 && (FromElevation == 0 || C->Elevation == 0 || FromElevation == C->Elevation || C->Elevation == 15);
}

void UEmeraldData::FinishSmoke(bool bSuccess, const FString& Message)
{
    bSmokeActive=false;
    bSuccess=bSuccess && SmokeWarps.Num()==13 && SmokeIndex==SmokeSteps.Num() && !SmokeSteps.IsEmpty();
    TSharedRef<FJsonObject> Report=MakeShared<FJsonObject>();
    Report->SetBoolField(TEXT("success"),bSuccess);
    Report->SetStringField(TEXT("scope"),TEXT("Actual grid-pawn inputs and map travel; story-state, NPC and rendered quality unverified"));
    Report->SetStringField(TEXT("message"),Message);
    Report->SetNumberField(TEXT("completed_input_steps"),SmokeIndex);
    Report->SetNumberField(TEXT("planned_input_steps"),SmokeSteps.Num());
    Report->SetNumberField(TEXT("distinct_actual_warp_links"),SmokeWarps.Num());
    FString Path=FPaths::ProjectSavedDir()/TEXT("Automation/traversal.json");
    FParse::Value(FCommandLine::Get(),TEXT("EmeraldSmokeReport="),Path);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
    FString Text;
    FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));
    FFileHelper::SaveStringToFile(Text,*Path);
    if(bSuccess) { UE_LOG(LogTemp,Display,TEXT("EMERALD_SMOKE PASS %s"),*Message); }
    else { UE_LOG(LogTemp,Error,TEXT("EMERALD_SMOKE FAIL %s"),*Message); }
    FPlatformMisc::RequestExitWithStatus(false,bSuccess?0:1);
}

void UEmeraldData::FinishEventSmoke(bool bSuccess,const FString& Message)
{
    bEventSmoke=false;
    auto Report=MakeShared<FJsonObject>();
    Report->SetBoolField(TEXT("success"),bSuccess);Report->SetStringField(TEXT("message"),Message);
    Report->SetStringField(TEXT("scope"),TEXT("APlayerController E/W key events, original sign/guard scripts and callback NPC state; diagnostic people, audio/emote presentation and physical hardware unverified"));
    Report->SetNumberField(TEXT("stage"),EventStage);
    if(Story)
    {
        Report->SetStringField(TEXT("last_source_error"),Story->LastError);
        Report->SetNumberField(TEXT("player_x"),Story->State.PlayerTile.X);Report->SetNumberField(TEXT("player_y"),Story->State.PlayerTile.Y);
        Report->SetNumberField(TEXT("twin_x"),Story->State.Objects[1].Tile.X);Report->SetNumberField(TEXT("twin_y"),Story->State.Objects[1].Tile.Y);
    }
    FString Path=FPaths::ProjectSavedDir()/TEXT("Automation/event-input.json");FParse::Value(FCommandLine::Get(),TEXT("EmeraldEventReport="),Path);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
    FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*Path);
    if(bSuccess){UE_LOG(LogTemp,Display,TEXT("EMERALD_EVENT_INPUT PASS %s"),*Message);}
    else {UE_LOG(LogTemp,Error,TEXT("EMERALD_EVENT_INPUT FAIL %s"),*Message);}
    FPlatformMisc::RequestExitWithStatus(false,bSuccess?0:1);
}

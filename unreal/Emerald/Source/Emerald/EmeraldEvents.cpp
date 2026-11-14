#include "EmeraldEvents.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
FIntPoint Direction(int32 D) { if(D==2)return {0,-1};if(D==3)return {-1,0};if(D==4)return {1,0};return {0,1}; }
FString ObjectKey(int32 I) {return FString::FromInt(I);}
}

bool FEmeraldEventRuntime::Load(const FString& Path,const TSharedPtr<FJsonObject>& Manifest,FString& Error)
{
    FString Text;TSharedPtr<FJsonObject> Program;
    if(!FFileHelper::LoadFileToString(Text,*Path) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Program) || !Program.IsValid())
    {Error=TEXT("Missing/invalid compiled source event program");return false;}
    if(Program->GetStringField(TEXT("schema"))!=TEXT("emerald.source-events/1") || Program->GetStringField(TEXT("source_revision"))!=Manifest->GetStringField(TEXT("source_revision")))
    {Error=TEXT("Event/source revision mismatch");return false;}
    for(const auto& Pair:Program->GetObjectField(TEXT("constants"))->Values) Constants.Add(FString(*Pair.Key),Pair.Value->AsNumber());
    for(const auto& Pair:Program->GetObjectField(TEXT("texts"))->Values) Texts.Add(FString(*Pair.Key),Pair.Value->AsString());
    for(const auto& Pair:Program->GetObjectField(TEXT("labels"))->Values)
    {
        const auto L=Pair.Value->AsObject();FEmeraldEventLabel Label;
        L->TryGetStringField(TEXT("next"),Label.Next);Label.Source=L->GetStringField(TEXT("source"));
        for(const auto& C:L->GetArrayField(TEXT("commands")))
        {
            const auto O=C->AsObject();FEmeraldEventCommand Cmd;Cmd.Op=O->GetStringField(TEXT("op"));Cmd.Line=O->GetIntegerField(TEXT("line"));
            for(const auto& A:O->GetArrayField(TEXT("args")))Cmd.Args.Add(A->AsString());
            Label.Commands.Add(MoveTemp(Cmd));
        }
        Labels.Add(FString(*Pair.Key),MoveTemp(Label));
    }
    for(const auto& Pair:Program->GetObjectField(TEXT("local_ids"))->Values)
    {
        TMap<FString,int32> Ids;for(const auto& P:Pair.Value->AsObject()->Values)Ids.Add(FString(*P.Key),P.Value->AsNumber());LocalIds.Add(FString(*Pair.Key),MoveTemp(Ids));
    }
    for(const auto& Pair:Program->GetObjectField(TEXT("callbacks"))->Values)
    {
        TMap<FString,FString> C;for(const auto& P:Pair.Value->AsObject()->Values)C.Add(FString(*P.Key),P.Value->AsString());Callbacks.Add(FString(*Pair.Key),MoveTemp(C));
    }
    for(const auto& F:Program->GetArrayField(TEXT("initial_flags")))
    {const auto* Value=Constants.Find(F->AsString());if(!Value){Error=TEXT("Unresolved initial flag");return false;}InitialFlags.Add(*Value);}
    MovementContract=Program->GetObjectField(TEXT("movement_contract"));
    for(const auto& M:Manifest->GetArrayField(TEXT("maps")))Maps.Add(M->AsObject()->GetStringField(TEXT("id")),M->AsObject());
    return true;
}

int32 FEmeraldEventRuntime::Literal(const FString& Token) const
{
    if(const auto* Locals=LocalIds.Find(State.Map))if(const auto* I=Locals->Find(Token))return *I;
    if(const auto* I=Constants.Find(Token))return *I;
    if(Token.StartsWith(TEXT("0x")))return FCString::Strtoi(*Token,nullptr,16);
    if(Token.IsNumeric() || Token.StartsWith(TEXT("-")))return FCString::Atoi(*Token);
    return INDEX_NONE;
}
int32 FEmeraldEventRuntime::Value(const FString& Token) const
{
    const int32 Number=Literal(Token);if(Number==INDEX_NONE)return INDEX_NONE;
    return Number>=0x4000 && Number<=0x8014 ? State.Vars.FindRef(Number) : Number;
}
uint16 FEmeraldEventRuntime::Var(const FString& Name) const {return State.Vars.FindRef(Literal(Name));}
void FEmeraldEventRuntime::SetVar(const FString& Name,int32 V) {State.Vars.Add(Literal(Name),static_cast<uint16>(V));++Revision;}
bool FEmeraldEventRuntime::Flag(const FString& Name) const {const int32 F=Literal(Name);return F>0&&State.Flags.Contains(F);}
void FEmeraldEventRuntime::SetFlag(const FString& Name,bool Set) {const int32 F=Literal(Name);if(Set)State.Flags.Add(F);else State.Flags.Remove(F);++Revision;}

void FEmeraldEventRuntime::Reset(int32 Gender,bool bAfterClock)
{
    State=FEmeraldSourceStore();State.Gender=Gender;MovementRng=MovementContract->GetIntegerField(TEXT("rng_seed"));AutonomousRemainder=0;
    State.PlayerName=Gender?TEXT("MAY"):TEXT("BRENDAN");State.RivalName=Gender?TEXT("BRENDAN"):TEXT("MAY");
    for(int32 F:InitialFlags)State.Flags.Add(F);
    State.Map=TEXT("MAP_LITTLEROOT_TOWN");
    RunImmediate(Gender?TEXT("InsideOfTruck_EventScript_SetIntroFlagsFemale"):TEXT("InsideOfTruck_EventScript_SetIntroFlagsMale"));
    // Explicit source checkpoint after the clock/broadcast sequence. Full arrival
    // remains available with bAfterClock=false; these fields cite that script path.
    if(bAfterClock)
    {
        SetVar(TEXT("VAR_LITTLEROOT_INTRO_STATE"),7);SetFlag(TEXT("FLAG_SET_WALL_CLOCK"),true);
        SetFlag(TEXT("FLAG_HIDE_LITTLEROOT_TOWN_PLAYERS_HOUSE_VIGOROTH_1"),true);
        SetFlag(TEXT("FLAG_HIDE_LITTLEROOT_TOWN_PLAYERS_HOUSE_VIGOROTH_2"),true);
        SetFlag(Gender?TEXT("FLAG_HIDE_LITTLEROOT_TOWN_MAYS_HOUSE_TRUCK"):TEXT("FLAG_HIDE_LITTLEROOT_TOWN_BRENDANS_HOUSE_TRUCK"),true);
        SetFlag(TEXT("FLAG_HIDE_LITTLEROOT_TOWN_FAT_MAN"),false);SetFlag(TEXT("FLAG_HIDE_MAP_NAME_POPUP"),false);SetFlag(TEXT("FLAG_SYS_TV_HOME"),true);
    }
    RequestedMap.Empty();VM=FEmeraldSourceVM();Dialogue.Empty();Pages.Empty();Effects.Empty();LastError.Empty();++Revision;
}

int32 FEmeraldEventRuntime::FacingFromMovement(const FString& M,int32 Fallback) const
{
    if(M.Contains(TEXT("FACE_UP")))return 2;if(M.Contains(TEXT("FACE_DOWN")))return 1;
    if(M.Contains(TEXT("FACE_LEFT")))return 3;if(M.Contains(TEXT("FACE_RIGHT")))return 4;return Fallback;
}

bool FEmeraldEventRuntime::EnterMap(const FString& Id,FIntPoint Tile)
{
    const auto* M=Maps.Find(Id);if(!M)return false;
    State.Map=Id;State.PlayerTile=Tile;State.PlayerDraw=FVector2D(Tile);State.PlayerPreviousTile=Tile;State.PlayerMoving=false;AutonomousRemainder=0;State.Objects.Empty();State.Moves.Empty();State.CellOverrides.Empty();State.Layout=(*M)->GetStringField(TEXT("layout"));
    int32 Index=1;
    for(const auto& Value:(*M)->GetArrayField(TEXT("object_events")))
    {
        const auto O=Value->AsObject();FEmeraldSourceObject Object;Object.Id=Index++;
        Object.Flag=Literal(O->GetStringField(TEXT("flag")));Object.Elevation=O->GetIntegerField(TEXT("elevation"));
        Object.Tile=FIntPoint(O->GetIntegerField(TEXT("x")),O->GetIntegerField(TEXT("y")));Object.Home=Object.PreviousTile=Object.Tile;Object.DrawTile=FVector2D(Object.Tile);
        Object.Range=FIntPoint(O->GetIntegerField(TEXT("movement_range_x")),O->GetIntegerField(TEXT("movement_range_y")));
        Object.Movement=O->GetStringField(TEXT("movement_type"));Object.Facing=FacingFromMovement(Object.Movement,1);Object.OriginalFacing=Object.Facing;
        if(MovementContract->GetObjectField(TEXT("initial_facing"))->HasField(Object.Movement))Object.Facing=Object.OriginalFacing=MovementContract->GetObjectField(TEXT("initial_facing"))->GetIntegerField(Object.Movement);
        if(MovementContract->GetObjectField(TEXT("has_range"))->HasField(Object.Movement))Object.Range=FIntPoint(FMath::Max(1,Object.Range.X),FMath::Max(1,Object.Range.Y));
        Object.GraphicsName=O->GetStringField(TEXT("graphics_id"));Object.Graphics=Literal(Object.GraphicsName);Object.Script=O->GetStringField(TEXT("script"));
        State.Objects.Add(Object.Id,MoveTemp(Object));
    }
    if(!Callback(TEXT("MAP_SCRIPT_ON_LOAD")) || !Callback(TEXT("MAP_SCRIPT_ON_TRANSITION")))return false;
    for(auto& Pair:State.Objects)
    {
        auto& O=Pair.Value;O.Visible=O.Flag==0||!State.Flags.Contains(O.Flag);O.DrawTile=FVector2D(O.Tile);
        if(O.Graphics>=240&&O.Graphics<=255)O.Graphics=State.Vars.FindRef(Literal(TEXT("VAR_OBJ_GFX_ID_0"))+O.Graphics-240);
    }
    VM.WaitingWarp=false;Callback(TEXT("MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE"),true);++Revision;return true;
}

bool FEmeraldEventRuntime::Callback(const FString& Type,bool Table)
{
    const auto* MapCallbacks=Callbacks.Find(State.Map);if(!MapCallbacks)return true;
    const auto* Label=MapCallbacks->Find(Type);if(!Label)return true;
    if(!Table)return RunImmediate(*Label);
    const auto* L=Labels.Find(*Label);if(!L)return false;
    for(const auto& C:L->Commands)
        if(C.Op==TEXT("map_script_2")&&C.Args.Num()==3&&Value(C.Args[0])==Value(C.Args[1]))
            return Type==TEXT("MAP_SCRIPT_ON_FRAME_TABLE")?Run(C.Args[2]):RunImmediate(C.Args[2]);
    return true;
}

bool FEmeraldEventRuntime::RunImmediate(const FString& Label)
{
    FEmeraldSourceVM Immediate;if(!Immediate.Start(*this,Label))return false;Immediate.Pump(0,true);return Immediate.Error.IsEmpty()&&!Immediate.Busy;
}
bool FEmeraldEventRuntime::Run(const FString& Label,int32 Interactor)
{
    if(VM.Busy)return false;State.Interactor=Interactor;SetVar(TEXT("VAR_LAST_TALKED"),Interactor);SetVar(TEXT("VAR_FACING"),State.PlayerFacing);return VM.Start(*this,Label);
}
void FEmeraldEventRuntime::Tick(float Seconds)
{
    if(!Enabled)return;TickAutonomous(Seconds);TickMoves(Seconds);VM.Pump(Seconds);
    if(!VM.Busy&&Dialogue.IsEmpty()&&RequestedMap.IsEmpty())Callback(TEXT("MAP_SCRIPT_ON_FRAME_TABLE"),true);
}

const FEmeraldSourceObject* FEmeraldEventRuntime::ObjectAt(FIntPoint Tile,int32 Elevation) const
{
    for(const auto& Pair:State.Objects)
    {const auto& O=Pair.Value;if(O.Visible&&O.Tile==Tile&&(Elevation==0||O.Elevation==0||O.Elevation==Elevation))return &O;}
    return nullptr;
}
bool FEmeraldEventRuntime::ObjectBlocked(FIntPoint Tile,int32 E) const
{
    if(ObjectAt(Tile,E))return true;
    for(const auto& P:State.Objects)
    {
        const auto& O=P.Value;if(!O.Visible || (E&&O.Elevation&&E!=O.Elevation))continue;
        if(O.AutonomousMoving && O.PreviousTile==Tile)return true;
        if(const auto* Move=State.Moves.Find(O.Id))
            if(Move->Duration>0 && (FIntPoint(FMath::RoundToInt(Move->Start.X),FMath::RoundToInt(Move->Start.Y))==Tile || FIntPoint(FMath::RoundToInt(Move->End.X),FMath::RoundToInt(Move->End.Y))==Tile))return true;
    }
    return false;
}
FString FEmeraldEventRuntime::CoordinateScript(FIntPoint Tile,int32 E) const
{
    const auto* M=Maps.Find(State.Map);if(!M)return {};
    for(const auto& V:(*M)->GetArrayField(TEXT("coord_events")))
    {
        const auto O=V->AsObject();if(O->GetIntegerField(TEXT("x"))!=Tile.X||O->GetIntegerField(TEXT("y"))!=Tile.Y)continue;
        const int32 Layer=O->GetIntegerField(TEXT("elevation"));if(Layer&&E&&Layer!=E)continue;
        if(Value(O->GetStringField(TEXT("var")))==Value(O->GetStringField(TEXT("var_value"))))return O->GetStringField(TEXT("script"));
    }
    return {};
}
FString FEmeraldEventRuntime::BackgroundScript(FIntPoint Tile,int32 Facing,int32 E) const
{
    const auto* M=Maps.Find(State.Map);if(!M)return {};
    for(const auto& V:(*M)->GetArrayField(TEXT("bg_events")))
    {
        const auto O=V->AsObject();if(O->GetIntegerField(TEXT("x"))!=Tile.X||O->GetIntegerField(TEXT("y"))!=Tile.Y)continue;
        const int32 Layer=O->GetIntegerField(TEXT("elevation"));if(Layer&&E&&Layer!=E)continue;
        FString Required;O->TryGetStringField(TEXT("player_facing_dir"),Required);
        if(Required.EndsWith(TEXT("NORTH"))&&Facing!=2)continue;if(Required.EndsWith(TEXT("SOUTH"))&&Facing!=1)continue;
        if(Required.EndsWith(TEXT("WEST"))&&Facing!=3)continue;if(Required.EndsWith(TEXT("EAST"))&&Facing!=4)continue;
        return O->GetStringField(TEXT("script"));
    }
    return {};
}

void FEmeraldEventRuntime::SetObjectTile(int32 Id,FIntPoint Tile,bool Permanent)
{
    if(Id==255){State.PlayerTile=Tile;State.PlayerDraw=FVector2D(Tile);}
    else if(auto* O=State.Objects.Find(Id)){O->PreviousTile=O->Tile=Tile;O->DrawTile=FVector2D(Tile);O->AutonomousMoving=false;O->AutonomousFrames=0;if(Permanent)O->Home=Tile;}
    ++Revision;
}
void FEmeraldEventRuntime::SetObjectFacing(int32 Id,int32 Facing)
{
    if(Id==255)State.PlayerFacing=Facing;else if(auto* O=State.Objects.Find(Id))O->Facing=Facing;++Revision;
}
bool FEmeraldEventRuntime::HasMove(int32 Id) const {return Id==0?!State.Moves.IsEmpty():State.Moves.Contains(Id);}

uint16 FEmeraldEventRuntime::NextMovementRandom()
{
    MovementRng=MovementRng*static_cast<uint32>(MovementContract->GetNumberField(TEXT("rng_multiplier")))+static_cast<uint32>(MovementContract->GetNumberField(TEXT("rng_increment")));
    return MovementRng>>16;
}
bool FEmeraldEventRuntime::AutonomousBusy() const
{
    for(const auto& Pair:State.Objects)if(Pair.Value.Visible&&Pair.Value.AutonomousMoving)return true;
    return false;
}
int32 FEmeraldEventRuntime::AutonomousCollision(const FEmeraldSourceObject& O,FIntPoint Target,int32 Facing) const
{
    if((O.Range.X && FMath::Abs(Target.X-O.Home.X)>O.Range.X) || (O.Range.Y && FMath::Abs(Target.Y-O.Home.Y)>O.Range.Y))return 1;
    const auto* Map=Maps.Find(State.Map);if(!Map)return 2;
    const auto G=(*Map)->GetObjectField(TEXT("geometry"));const int32 W=G->GetIntegerField(TEXT("width")),H=G->GetIntegerField(TEXT("height"));
    auto Cell=[&](FIntPoint P)->TSharedPtr<FJsonObject>{return P.X>=0&&P.Y>=0&&P.X<W&&P.Y<H?G->GetArrayField(TEXT("cells"))[P.Y*W+P.X]->AsObject():nullptr;};
    const auto C=Cell(Target),From=Cell(O.Tile);if(!C.IsValid()||!From.IsValid())return 2;
    const uint16* Override=State.CellOverrides.Find(Target);const int32 Collision=Override?(*Override>>10)&3:C->GetIntegerField(TEXT("collision"));
    if(Collision)return 2;
    const auto Blocks=MovementContract->GetObjectField(TEXT("blocked_behaviors"));
    auto Blocked=[&](const TCHAR* Name,int32 Behavior){for(const auto& B:Blocks->GetArrayField(Name))if(static_cast<int32>(B->AsNumber())==Behavior)return true;return false;};
    const TCHAR* Exit=Facing==1?TEXT("south"):Facing==2?TEXT("north"):Facing==3?TEXT("west"):TEXT("east");
    const TCHAR* Entry=Facing==1?TEXT("north"):Facing==2?TEXT("south"):Facing==3?TEXT("east"):TEXT("west");
    if(Blocked(Exit,From->GetIntegerField(TEXT("behavior")))||Blocked(Entry,C->GetIntegerField(TEXT("behavior"))))return 2;
    const int32 Elevation=Override?*Override>>12:C->GetIntegerField(TEXT("elevation"));
    if(O.Elevation && Elevation && Elevation!=15 && O.Elevation!=Elevation)return 3;
    for(const auto& Pair:State.Objects)
    {
        const auto& Other=Pair.Value;if(Other.Id==O.Id||!Other.Visible||(O.Elevation&&Other.Elevation&&O.Elevation!=Other.Elevation))continue;
        if(Other.Tile==Target || (Other.AutonomousMoving&&Other.PreviousTile==Target))return 4;
        if(const auto* Move=State.Moves.Find(Other.Id))if(Move->Duration>0 && (FVector2D(Target).Equals(Move->Start)||FVector2D(Target).Equals(Move->End)))return 4;
    }
    const auto PlayerCell=Cell(State.PlayerTile);const int32 PlayerE=PlayerCell.IsValid()?PlayerCell->GetIntegerField(TEXT("elevation")):0;
    if(!State.PlayerHidden && (!O.Elevation||!PlayerE||O.Elevation==PlayerE) && (State.PlayerTile==Target||(State.PlayerMoving&&State.PlayerPreviousTile==Target)))return 4;
    if(const auto* Move=State.Moves.Find(255))if(Move->Duration>0 && (FVector2D(Target).Equals(Move->Start)||FVector2D(Target).Equals(Move->End)))return 4;
    return 0;
}
void FEmeraldEventRuntime::TickAutonomous(float Seconds)
{
    // Source movement is frame-counted. Carry fractional frames and use stable
    // object-slot order so pacing/random calls do not depend on render frame rate.
    AutonomousRemainder+=FMath::Max(0.f,Seconds)*MovementContract->GetIntegerField(TEXT("frames_per_second"));
    const int32 Frames=FMath::FloorToInt(AutonomousRemainder+1e-6);AutonomousRemainder-=Frames;
    TArray<int32> Ids;State.Objects.GetKeys(Ids);Ids.Sort();
    const int32 WalkFrames=MovementContract->GetIntegerField(TEXT("walk_frames"));
    auto NewDelay=[&](){const auto& Delays=MovementContract->GetArrayField(TEXT("delay_frames"));return static_cast<int32>(Delays[NextMovementRandom()%Delays.Num()]->AsNumber());};
    for(int32 Frame=0;Frame<Frames;++Frame)for(int32 Id:Ids)
    {
        auto& O=State.Objects[Id];if(!O.Visible||State.Moves.Contains(Id))continue;
        if(O.AutonomousMoving)
        {
            ++O.AutonomousFrames;O.DrawTile=FMath::Lerp(FVector2D(O.PreviousTile),FVector2D(O.Tile),FMath::Clamp(static_cast<float>(O.AutonomousFrames)/WalkFrames,0.f,1.f));++Revision;
            if(O.AutonomousFrames>=WalkFrames){O.DrawTile=FVector2D(O.Tile);O.PreviousTile=O.Tile;O.AutonomousMoving=false;O.AutonomousFrames=0;O.AutonomousDelay=-1;++O.AutonomousSteps;
                UE_LOG(LogTemp,Display,TEXT("EMERALD_AUTONOMOUS_STEP map=%s id=%d tile=%d,%d steps=%d"),*State.Map,Id,O.Tile.X,O.Tile.Y,O.AutonomousSteps);}
            continue;
        }
        // New decisions pause during a script/dialogue; an already reserved step
        // finishes before lock/lockall advances. Scoped conservative script lock.
        if(IsLocked()||!RequestedMap.IsEmpty())continue;
        const bool Wander=O.Movement.StartsWith(TEXT("MOVEMENT_TYPE_WANDER_")),Look=O.Movement==TEXT("MOVEMENT_TYPE_LOOK_AROUND");
        if(!Wander&&!Look)continue;
        if(O.AutonomousDelay<0){O.AutonomousDelay=NewDelay();continue;}
        if(--O.AutonomousDelay>0)continue;
        const bool Horizontal=O.Movement.Contains(TEXT("LEFT_AND_RIGHT"))||O.Movement.Contains(TEXT("RIGHT_AND_LEFT"));
        const bool Vertical=O.Movement.Contains(TEXT("UP_AND_DOWN"))||O.Movement.Contains(TEXT("DOWN_AND_UP"));
        const auto& Directions=MovementContract->GetArrayField(Horizontal?TEXT("horizontal_directions"):Vertical?TEXT("vertical_directions"):TEXT("directions"));
        const int32 Facing=Directions[NextMovementRandom()%Directions.Num()]->AsNumber();if(!O.FacingLocked)O.Facing=Facing;++Revision;
        O.AutonomousDelay=-1;
        if(Look||AutonomousCollision(O,O.Tile+Direction(Facing),Facing))continue;
        O.PreviousTile=O.Tile;O.Tile+=Direction(Facing);O.AutonomousMoving=true;O.AutonomousFrames=0;
    }
}

FString FEmeraldEventRuntime::FormatText(const FString& Label) const
{
    const FString* Source=Texts.Find(Label);if(!Source)return {};
    FString Text=*Source;Text.ReplaceInline(TEXT("{PLAYER}"),*State.PlayerName);Text.ReplaceInline(TEXT("{RIVAL}"),*State.RivalName);
    for(const auto& Pair:State.Buffers)Text.ReplaceInline(*FString::Printf(TEXT("{%s}"),*Pair.Key),*Pair.Value);
    Text.ReplaceInline(TEXT("{A_BUTTON}"),TEXT("A"));Text.ReplaceInline(TEXT("{B_BUTTON}"),TEXT("B"));return Text;
}
void FEmeraldEventRuntime::ShowText(const FString& Label,bool bYesNo)
{
    const FString Text=FormatText(Label);Pages.Empty();Text.ParseIntoArray(Pages,TEXT("\f"),false);Page=0;YesNo=bYesNo;Dialogue=Pages.IsEmpty()?Text:Pages[0];
}
void FEmeraldEventRuntime::AdvanceDialogue(bool Answer)
{
    if(Page+1<Pages.Num()){Dialogue=Pages[++Page];return;}
    if(YesNo)SetVar(TEXT("VAR_RESULT"),Answer?1:0);Dialogue.Empty();VM.WaitingDialogue=false;VM.Pump(0);++Revision;
}
void FEmeraldEventRuntime::ConfirmClock(int32 Hour,int32 Minute)
{
    if(!ClockReadOnly){State.Hour=(Hour%24+24)%24;State.Minute=(Minute%60+60)%60;}
    VM.WaitingClock=false;VM.Pump(0);++Revision;
}
void FEmeraldEventRuntime::Emit(const FString& Kind,const TArray<FString>& Args)
{
    auto E=MakeShared<FJsonObject>();E->SetStringField(TEXT("kind"),Kind);TArray<TSharedPtr<FJsonValue>> A;
    for(const auto& Arg:Args)A.Add(MakeShared<FJsonValueString>(Arg));E->SetArrayField(TEXT("args"),A);Effects.Add(E);EmittedEffectKinds.Add(Kind);
}

bool FEmeraldEventRuntime::Special(const FString& Name,const FString& ResultVar,FEmeraldSourceVM& Machine)
{
    if(Name==TEXT("GetPlayerBigGuyGirlString")){State.Buffers.Add(TEXT("STR_VAR_1"),State.Gender?TEXT("big girl"):TEXT("big guy"));return true;}
    if(Name==TEXT("GetRivalSonDaughterString")){State.Buffers.Add(TEXT("STR_VAR_1"),State.Gender?TEXT("son"):TEXT("daughter"));return true;}
    if(Name==TEXT("InitSecretBaseDecorationSprites"))return true; // Empty new-game decoration inventory only.
    if(Name==TEXT("HasAllHoennMons")){SetVar(ResultVar,0);return true;}
    if(Name==TEXT("StartWallClock")||Name==TEXT("Special_ViewWallClock"))
    {ClockReadOnly=Name==TEXT("Special_ViewWallClock");Machine.WaitingClock=true;return true;}
    if(Name==TEXT("DoPCTurnOnEffect")||Name==TEXT("DoPCTurnOffEffect")||Name==TEXT("TurnOffTVScreen")||Name==TEXT("TurnOnTVScreen"))
    {Emit(Name,{});return true;}
    return false;
}

bool FEmeraldEventRuntime::StartMovement(int32 Id,const FString& Label,FString& Error)
{
    if(!Labels.Contains(Label)){Error=TEXT("Missing movement label ")+Label;return false;}
    if(Id!=255&&!State.Objects.Contains(Id)){Error=TEXT("Unknown current-map object ID ")+ObjectKey(Id);return false;}
    FEmeraldSourceMove Move;Move.Id=Id;Move.Label=Label;State.Moves.Add(Id,Move);
    if(auto* O=State.Objects.Find(Id))O->OriginalFacing=O->Facing;return true;
}
void FEmeraldEventRuntime::TickMoves(float Seconds)
{
    TArray<int32> Finished;
    for(auto& Pair:State.Moves)
    {
        auto& M=Pair.Value;float Time=Seconds;
        auto Position=[&](){return M.Id==255?State.PlayerDraw:State.Objects[M.Id].DrawTile;};
        auto Put=[&](FVector2D P){if(M.Id==255)State.PlayerDraw=P;else State.Objects[M.Id].DrawTile=P;};
        for(int32 Guard=0;Guard<100;++Guard)
        {
            if(M.Duration>0)
            {
                const float Used=FMath::Min(Time,M.Duration-M.Elapsed);M.Elapsed+=Used;Time-=Used;
                Put(FMath::Lerp(M.Start,M.End,FMath::Clamp(M.Elapsed/M.Duration,0.f,1.f)));
                if(M.Elapsed+KINDA_SMALL_NUMBER<M.Duration)break;
                SetObjectTile(M.Id,FIntPoint(FMath::RoundToInt(M.End.X),FMath::RoundToInt(M.End.Y)),false);M.Duration=0;
                if(Time<=0)break;
            }
            const auto* L=Labels.Find(M.Label);if(!L||M.Index>=L->Commands.Num()){Finished.Add(M.Id);break;}
            const auto C=L->Commands[M.Index++];const FString Op=C.Op;
            if(Op==TEXT("step_end")){Finished.Add(M.Id);break;}
            int32 Face=0;
            if(Op.EndsWith(TEXT("_down")))Face=1;else if(Op.EndsWith(TEXT("_up")))Face=2;else if(Op.EndsWith(TEXT("_left")))Face=3;else if(Op.EndsWith(TEXT("_right")))Face=4;
            M.Start=M.End=Position();M.Elapsed=0;M.Walking=false;
            if(Op.StartsWith(TEXT("delay_")))M.Duration=FCString::Atof(*Op.Mid(6))/60.f;
            else if(Op==TEXT("face_player"))
            {
                const FIntPoint D=State.PlayerTile-State.Objects[M.Id].Tile;SetObjectFacing(M.Id,FMath::Abs(D.X)>FMath::Abs(D.Y)?(D.X>0?4:3):(D.Y>0?1:2));
            }
            else if(Op==TEXT("face_original_direction"))SetObjectFacing(M.Id,State.Objects[M.Id].OriginalFacing);
            else if(Op==TEXT("lock_facing_direction")||Op==TEXT("unlock_facing_direction"))
            {
                const bool Lock=Op==TEXT("lock_facing_direction");
                if(M.Id==255)State.PlayerFacingLocked=Lock;else State.Objects[M.Id].FacingLocked=Lock;
            }
            else if(Op.StartsWith(TEXT("face_"))&&Face)SetObjectFacing(M.Id,Face);
            else if(Op.StartsWith(TEXT("walk_"))&&Face)
            {
                M.Walking=true;
                const bool Locked=M.Id==255?State.PlayerFacingLocked:State.Objects[M.Id].FacingLocked;
                if(!Locked)SetObjectFacing(M.Id,Face);
                if(!Op.StartsWith(TEXT("walk_in_place")))M.End+=FVector2D(Direction(Face));
                const float Frames=Op.Contains(TEXT("in_place_faster"))?4:Op.Contains(TEXT("fastest"))?2:Op.Contains(TEXT("faster"))?4:Op.Contains(TEXT("fast"))?8:16;
                M.Duration=Frames/60.f;
            }
            else if(Op.StartsWith(TEXT("emote_"))||Op.StartsWith(TEXT("jump_in_place"))||Op.Contains(TEXT("ground_effect")))
            {Emit(Op,{ObjectKey(M.Id)});M.Duration=Op.StartsWith(TEXT("emote_"))?32.f/60.f:0;}
            else {LastError=TEXT("Unsupported movement ")+Op;Unsupported.Add(Op);Finished.Add(M.Id);break;}
            if(M.Duration>0&&Time<=0)break;
        }
    }
    for(int32 I:Finished)State.Moves.Remove(I);
}

bool FEmeraldSourceVM::Start(FEmeraldEventRuntime& Runtime,const FString& Label)
{
    Owner=&Runtime;Before=Runtime.State;EffectsBefore=Runtime.Effects.Num();RequestedBefore=Runtime.RequestedMap;RequestedTileBefore=Runtime.RequestedTile;Root=Label;Error.Empty();Delay=0;WaitMove=-1;WaitingDialogue=WaitingClock=WaitingWarp=false;
    if(!Runtime.Labels.Contains(Label)){Fail(TEXT("Missing script ")+Label);return false;}
    Stack={{Label,0}};Busy=true;return true;
}
void FEmeraldSourceVM::Fail(const FString& Why)
{
    Error=Why;Busy=false;Stack.Empty();
    if(Owner){Owner->State=Before;Owner->Effects.SetNum(EffectsBefore);Owner->RequestedMap=RequestedBefore;Owner->RequestedTile=RequestedTileBefore;Owner->Dialogue.Empty();Owner->LastError=Why;Owner->Unsupported.Add(Why);++Owner->Revision;}
    UE_LOG(LogTemp,Warning,TEXT("EMERALD_SOURCE unsupported/rollback %s: %s"),*Root,*Why);
}
void FEmeraldSourceVM::Pump(float Seconds,bool bImmediate)
{
    if(!Busy||!Owner)return;
    auto& R=*Owner;
    if(WaitingDialogue||WaitingClock||WaitingWarp)return;
    if(WaitMove>=0){if(R.HasMove(WaitMove))return;WaitMove=-1;}
    if(Delay>0){Delay=FMath::Max(0.f,Delay-Seconds);if(Delay>0)return;}
    for(int32 Guard=0;Guard<10000&&Busy;++Guard)
    {
        if(Stack.IsEmpty()){Busy=false;break;}
        auto& Cursor=Stack.Last();const auto* L=R.Labels.Find(Cursor.Label);
        if(!L){Fail(TEXT("Missing label ")+Cursor.Label);return;}
        if(Cursor.Index>=L->Commands.Num())
        {if(!L->Next.IsEmpty()&&R.Labels.Contains(L->Next)){Cursor={L->Next,0};continue;}Stack.Pop();continue;}
        const auto C=L->Commands[Cursor.Index++];const FString Op=C.Op;const auto& A=C.Args;
        R.Executed.FindOrAdd(Op)++;R.Trace.Add(Cursor.Label+TEXT(":")+FString::FromInt(C.Line)+TEXT(" ")+Op);
        auto Require=[&](int32 Count){if(A.Num()<Count){Fail(TEXT("Missing arguments ")+Op);return false;}return true;};
        auto Number=[&](int32 I){const int32 V=R.Value(A[I]);if(V==INDEX_NONE)Fail(TEXT("Unknown numeric symbol ")+A[I]);return V;};
        auto Jump=[&](const FString& Target,bool Call){if(!R.Labels.Contains(Target)){Fail(TEXT("Missing branch ")+Target);return;}if(Call)Stack.Add({Target,0});else Stack.Last()={Target,0};};
        if(Op==TEXT("end")){Busy=false;Stack.Empty();break;}
        if(Op==TEXT("return")){Stack.Pop();continue;}
        if(Op==TEXT("goto")||Op==TEXT("call")){if(!Require(1))return;Jump(A[0],Op==TEXT("call"));continue;}
        if(Op.StartsWith(TEXT("goto_if_"))||Op.StartsWith(TEXT("call_if_")))
        {
            const bool Call=Op.StartsWith(TEXT("call_"));const FString Condition=Op.Mid(Call?8:8);bool Take=false;FString Target;
            if(Condition==TEXT("set")||Condition==TEXT("unset"))
            {if(!Require(2))return;Take=R.Flag(A[0])==(Condition==TEXT("set"));Target=A[1];}
            else
            {if(!Require(3))return;const int32 X=Number(0),Y=Number(1);if(!Busy)return;Target=A[2];
             Take=Condition==TEXT("eq")?X==Y:Condition==TEXT("ne")?X!=Y:Condition==TEXT("lt")?X<Y:Condition==TEXT("le")?X<=Y:Condition==TEXT("ge")?X>=Y:Condition==TEXT("gt")?X>Y:false;}
            if(Take)Jump(Target,Call);continue;
        }
        if(Op==TEXT("setvar")||Op==TEXT("copyvar")||Op==TEXT("addvar")||Op==TEXT("subvar"))
        {if(!Require(2))return;const int32 V=Number(1);if(!Busy)return;R.SetVar(A[0],Op==TEXT("addvar")?R.Var(A[0])+V:Op==TEXT("subvar")?R.Var(A[0])-V:V);continue;}
        if(Op==TEXT("setflag")||Op==TEXT("clearflag")){if(!Require(1))return;if(R.Literal(A[0])==INDEX_NONE){Fail(TEXT("Unknown flag ")+A[0]);return;}R.SetFlag(A[0],Op==TEXT("setflag"));continue;}
        if(Op==TEXT("checkplayergender")){R.SetVar(TEXT("VAR_RESULT"),R.State.Gender);continue;}
        if(Op==TEXT("getpartysize")){R.SetVar(TEXT("VAR_RESULT"),R.State.PartyCount);continue;}
        if(Op==TEXT("getplayerxy")){if(!Require(2))return;R.SetVar(A[0],R.State.PlayerTile.X);R.SetVar(A[1],R.State.PlayerTile.Y);continue;}
        if(Op==TEXT("setobjectxyperm")||Op==TEXT("setobjectxy"))
        {if(!Require(3))return;const int32 Id=Number(0),X=Number(1),Y=Number(2);if(!Busy)return;R.SetObjectTile(Id,{X,Y},Op.EndsWith(TEXT("perm")));continue;}
        if(Op==TEXT("setobjectmovementtype"))
        {if(!Require(2))return;const int32 Id=Number(0);if(auto* O=R.State.Objects.Find(Id)){O->Movement=A[1];O->Facing=R.FacingFromMovement(A[1],O->Facing);}continue;}
        if(Op==TEXT("turnobject")){if(!Require(2))return;const int32 Id=Number(0),F=Number(1);if(!Busy)return;R.SetObjectFacing(Id,F);continue;}
        if(Op==TEXT("addobject")||Op==TEXT("removeobject")||Op==TEXT("hideobjectat"))
        {if(!Require(1))return;if(Op==TEXT("hideobjectat")&&A.Num()>1&&A[1]!=R.State.Map){R.Emit(Op,A);continue;}const int32 Id=Number(0);if(auto* O=R.State.Objects.Find(Id))O->Visible=Op==TEXT("addobject");continue;}
        if(Op==TEXT("faceplayer"))
        {if(auto* O=R.State.Objects.Find(R.State.Interactor)){const FIntPoint D=R.State.PlayerTile-O->Tile;R.SetObjectFacing(O->Id,FMath::Abs(D.X)>FMath::Abs(D.Y)?(D.X>0?4:3):(D.Y>0?1:2));}continue;}
        if(Op==TEXT("msgbox")||Op==TEXT("message"))
        {
            if(!Require(1))return;if(!R.Texts.Contains(A[0])){Fail(TEXT("Missing source text ")+A[0]);return;}
            if(bImmediate){Fail(TEXT("Asynchronous text in immediate callback"));return;}
            R.ShowText(A[0],A.Num()>1&&A[1]==TEXT("MSGBOX_YESNO"));if(Op==TEXT("msgbox")){WaitingDialogue=true;return;}continue;
        }
        if(Op==TEXT("waitbuttonpress")){WaitingDialogue=true;return;}
        if(Op==TEXT("closemessage")){R.Dialogue.Empty();continue;}
        if(Op==TEXT("delay")){if(!Require(1))return;Delay=Number(0)/60.f;if(bImmediate&&Delay>0){Fail(TEXT("Delay in immediate callback"));return;}if(Delay>0)return;continue;}
        if(Op==TEXT("applymovement")||Op==TEXT("applywaitmovement"))
        {if(!Require(2))return;FString Why;const int32 Id=Number(0);if(!R.StartMovement(Id,A[1],Why)){Fail(Why);return;}if(Op==TEXT("applywaitmovement")){if(bImmediate){Fail(TEXT("Movement in immediate callback"));return;}WaitMove=Id;return;}continue;}
        if(Op==TEXT("waitmovement")){WaitMove=A.IsEmpty()?0:Number(0);if(R.HasMove(WaitMove))return;WaitMove=-1;continue;}
        if(Op==TEXT("special")||Op==TEXT("specialvar"))
        {if(!Require(Op==TEXT("specialvar")?2:1))return;const FString Name=A[Op==TEXT("specialvar")?1:0];if(!R.Special(Name,Op==TEXT("specialvar")?A[0]:FString(),*this)){Fail(TEXT("Unimplemented source special ")+Name);return;}if(WaitingClock){if(bImmediate){Fail(TEXT("Clock UI in immediate callback"));}return;}continue;}
        if(Op==TEXT("setmaplayoutindex")){if(!Require(1))return;R.State.Layout=A[0];++R.Revision;continue;}
        if(Op==TEXT("setmetatile"))
        {if(!Require(4))return;const int32 X=Number(0),Y=Number(1),M=Number(2),Collision=Number(3);if(!Busy)return;R.State.CellOverrides.Add({X,Y},static_cast<uint16>((M&1023)|(Collision?0xC00:0)));++R.Revision;continue;}
        if(Op==TEXT("warp")||Op==TEXT("warpsilent")||Op==TEXT("setdynamicwarp"))
        {if(!Require(3))return;const int32 X=Number(1),Y=Number(2);if(!Busy)return;R.RequestedMap=A[0];R.RequestedTile={X,Y};if(Op!=TEXT("setdynamicwarp")){WaitingWarp=true;return;}continue;}
        if(Op==TEXT("hideplayer")||Op==TEXT("showplayer")){R.State.PlayerHidden=Op==TEXT("hideplayer");continue;}
        if((Op==TEXT("lock")||Op==TEXT("lockall")) && R.AutonomousBusy())
        {--Stack.Last().Index;Delay=1.f/60.f;return;}
        if(Op==TEXT("lock")||Op==TEXT("lockall")||Op==TEXT("release")||Op==TEXT("releaseall")||Op==TEXT("waitstate")||Op==TEXT("waitmessage"))continue;
        if(Op==TEXT("playse")||Op==TEXT("playbgm")||Op==TEXT("savebgm")||Op==TEXT("fadedefaultbgm")||Op==TEXT("playfanfare")||Op==TEXT("opendoor")||Op==TEXT("closedoor")||Op==TEXT("fadescreen")||Op==TEXT("setrespawn")||Op==TEXT("incrementgamestat"))
        {R.Emit(Op,A);continue;}
        if(Op==TEXT("waitse")||Op==TEXT("waitfanfare")||Op==TEXT("waitdooranim"))
        {R.Emit(Op,A);continue;} // Effect timing/output is an explicit pending bridge, never a parity claim.
        Fail(TEXT("Unsupported source opcode ")+Op);return;
    }
    if(Busy&&!WaitingDialogue&&!WaitingClock&&!WaitingWarp&&Delay<=0&&WaitMove<0)Fail(TEXT("Instruction budget exhausted"));
}

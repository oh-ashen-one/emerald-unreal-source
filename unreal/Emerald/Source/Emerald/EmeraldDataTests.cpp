#include "EmeraldData.h"
#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "Engine/GameInstance.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEmeraldManifestTest, "Emerald.Data.SourceManifest", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEmeraldManifestTest::RunTest(const FString& Parameters)
{
    auto* Instance = NewObject<UGameInstance>();
    auto* Data = NewObject<UEmeraldData>(Instance);
    FString Error;
    if (!TestTrue(TEXT("Load source-derived manifest"), Data->Load(FPaths::ProjectContentDir()/TEXT("Imported/Data/littleroot.json"), Error)))
    { AddError(Error); return false; }
    TestEqual(TEXT("Every requested map"), Data->AllMaps().Num(), 6);
    int32 CellCount = 0, WarpCount = 0;
    for (const auto& Pair : Data->AllMaps())
    {
        const auto& M = Pair.Value;
        CellCount += M.Cells.Num();
        for (int32 Y=0;Y<M.Height;++Y) for(int32 X=0;X<M.Width;++X)
        {
            const auto* C = M.Cell({X,Y});
            TestEqual(TEXT("Collision blocks base-grid entry"), Data->CanEnter(M.Id,{X,Y},C->Elevation),C->Collision==0);
        }
        TestFalse(TEXT("West boundary blocked"),Data->CanEnter(M.Id,{-1,0},0));
        TestFalse(TEXT("South boundary blocked"),Data->CanEnter(M.Id,{0,M.Height},0));
        for(int32 I=0;I<M.Warps.Num();++I)
        {
            FString Target; FIntPoint Tile;
            TestTrue(TEXT("Resolve source warp"),Data->ResolveWarp(M.Id,I,Target,Tile));
            const auto& W=M.Warps[I];
            const auto* Dest=Data->Map(W.Destination);
            TestEqual(TEXT("Destination ID"),Target,W.Destination);
            TestEqual(TEXT("Destination zero-based warp tile"),Tile,Dest->Warps[W.DestinationIndex].Tile);
            ++WarpCount;
        }
    }
    TestEqual(TEXT("Source cells"),CellCount,911);
    TestEqual(TEXT("Warp links"),WarpCount,13);
    FString Target; FIntPoint Tile;
    TestFalse(TEXT("Invalid index fails"),Data->ResolveWarp(TEXT("MAP_LITTLEROOT_TOWN"),99,Target,Tile));
    return true;
}
#endif

#include "EmeraldEvents.h"
#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
bool LoadRuntime(FEmeraldEventRuntime& Runtime)
{
    FString Text,Error;TSharedPtr<FJsonObject> Root;
    FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Imported/Data/littleroot.json")));
    if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root))return false;
    return Runtime.Load(FPaths::ProjectContentDir()/TEXT("Imported/Data/source-events.json"),Root,Error);
}
void Drive(FEmeraldEventRuntime& R)
{
    for(int32 I=0;I<10000 && R.VM.Busy;++I)
    {
        if(R.VM.WaitingDialogue)R.AdvanceDialogue();
        if(R.VM.WaitingClock)R.ConfirmClock(13,37);
        R.Tick(1.f/60.f);
    }
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEmeraldSourceCallbacks,"Emerald.Events.CallbacksAndVisibility",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEmeraldSourceCallbacks::RunTest(const FString& Parameters)
{
    FEmeraldEventRuntime R;if(!TestTrue(TEXT("Load source program"),LoadRuntime(R)))return false;
    R.Reset(0,true);TestTrue(TEXT("Enter town source callbacks"),R.EnterMap(TEXT("MAP_LITTLEROOT_TOWN"),{10,10}));
    TestEqual(TEXT("Original transition moves twin to route guard"),R.State.Objects[1].Tile,FIntPoint(7,2));
    TestEqual(TEXT("Guard faces down"),R.State.Objects[1].Facing,1);
    TestEqual(TEXT("Rival gfx follows source gender helper"),static_cast<int32>(R.Var(TEXT("VAR_OBJ_GFX_ID_0"))),R.Constants[TEXT("OBJ_EVENT_GFX_RIVAL_MAY_NORMAL")]);
    TestTrue(TEXT("Twin visible"),R.State.Objects[1].Visible);
    TestTrue(TEXT("Fat man appears after truck intro"),R.State.Objects[2].Visible);
    TestFalse(TEXT("Outside mom hidden at after-clock checkpoint"),R.State.Objects[4].Visible);
    TestTrue(TEXT("Guard source collision"),R.ObjectBlocked({7,2},3));
    TestTrue(TEXT("Enter own room callbacks"),R.EnterMap(TEXT("MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F"),{7,1}));
    for(int32 I=2;I<=13;++I)TestFalse(TEXT("Unused decoration slots not populated"),R.State.Objects[I].Visible);
    R.Reset(1,true);R.EnterMap(TEXT("MAP_LITTLEROOT_TOWN"),{10,10});
    TestEqual(TEXT("Female player's rival gfx"),static_cast<int32>(R.Var(TEXT("VAR_OBJ_GFX_ID_0"))),R.Constants[TEXT("OBJ_EVENT_GFX_RIVAL_BRENDAN_NORMAL")]);
    TestFalse(TEXT("Other player's mother remains hidden"),R.Flag(TEXT("FLAG_HIDE_LITTLEROOT_TOWN_MAYS_HOUSE_MOM")));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEmeraldAllMapCallbacks,"Emerald.Events.AllSixMapCallbacks",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEmeraldAllMapCallbacks::RunTest(const FString& Parameters)
{
    FEmeraldEventRuntime R;if(!LoadRuntime(R))return false;
    const TArray<FString> Maps={TEXT("MAP_LITTLEROOT_TOWN"),TEXT("MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_1F"),TEXT("MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F"),TEXT("MAP_LITTLEROOT_TOWN_MAYS_HOUSE_1F"),TEXT("MAP_LITTLEROOT_TOWN_MAYS_HOUSE_2F"),TEXT("MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB")};
    for(int32 Gender=0;Gender<2;++Gender)
    {
        R.Reset(Gender,true);
        for(const auto& Map:Maps)
        {
            TestTrue(*Map,R.EnterMap(Map,{5,5}));TestTrue(*R.LastError,R.LastError.IsEmpty());TestEqual(TEXT("Actual source map state"),R.State.Map,Map);
            if(Map.EndsWith(TEXT("BIRCHS_LAB")))
            {TestTrue(TEXT("Unconditional original lab aide visible"),R.State.Objects[1].Visible);TestEqual(TEXT("Original aide graphics"),R.State.Objects[1].Graphics,R.Constants[TEXT("OBJ_EVENT_GFX_SCIENTIST_1")]);}
        }
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEmeraldSourceClock,"Emerald.Events.OriginalClockScript",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEmeraldSourceClock::RunTest(const FString& Parameters)
{
    for(int32 Gender=0;Gender<2;++Gender)
    {
        FEmeraldEventRuntime R;if(!LoadRuntime(R))return false;R.Reset(Gender,false);R.SetVar(TEXT("VAR_LITTLEROOT_INTRO_STATE"),4);
        const FString Map=Gender?TEXT("MAP_LITTLEROOT_TOWN_MAYS_HOUSE_2F"):TEXT("MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F");
        TestTrue(TEXT("Room callback sets clock stair gate"),R.EnterMap(Map,Gender?FIntPoint(1,1):FIntPoint(7,1)));
        TestEqual(TEXT("Source intro gate state"),static_cast<int32>(R.Var(TEXT("VAR_LITTLEROOT_INTRO_STATE"))),5);
        const FString Script=R.BackgroundScript(Gender?FIntPoint(3,1):FIntPoint(5,1),2,3);
        TestTrue(TEXT("Clock resolves source BG event"),!Script.IsEmpty());
        TestTrue(TEXT("Run original clock script"),R.Run(Script));Drive(R);
        TestFalse(TEXT("Original sequence terminates"),R.VM.Busy);
        TestTrue(TEXT("Clock script no unsupported opcode"),R.LastError.IsEmpty());
        TestTrue(TEXT("Source clock flag set"),R.Flag(TEXT("FLAG_SET_WALL_CLOCK")));
        TestEqual(TEXT("Source intro state after setting clock"),static_cast<int32>(R.Var(TEXT("VAR_LITTLEROOT_INTRO_STATE"))),6);
        TestTrue(TEXT("Source mover 1 hidden for next map load"),R.Flag(TEXT("FLAG_HIDE_LITTLEROOT_TOWN_PLAYERS_HOUSE_VIGOROTH_1")));
        TestEqual(TEXT("Native clock selection"),R.State.Hour,13);TestEqual(TEXT("Native clock minutes"),R.State.Minute,37);
        const int32 Mom=R.LocalIds[Map][TEXT("LOCALID_PLAYERS_HOUSE_2F_MOM")];TestFalse(TEXT("Mom leaves upstairs after original sequence"),R.State.Objects[Mom].Visible);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEmeraldSourceInteractions,"Emerald.Events.SourceTriggersAndRollback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEmeraldSourceInteractions::RunTest(const FString& Parameters)
{
    FEmeraldEventRuntime R;if(!LoadRuntime(R))return false;R.Reset();R.EnterMap(TEXT("MAP_LITTLEROOT_TOWN"),{10,10});
    TestEqual(TEXT("Original left route trigger"),R.CoordinateScript({10,1},3),FString(TEXT("LittlerootTown_EventScript_NeedPokemonTriggerLeft")));
    R.SetVar(TEXT("VAR_LITTLEROOT_TOWN_STATE"),1);
    TestTrue(TEXT("Old left guard predicate no longer active"),R.CoordinateScript({10,1},3).IsEmpty());
    TestEqual(TEXT("State-one Birch trigger at right tile"),R.CoordinateScript({11,1},3),FString(TEXT("LittlerootTown_EventScript_GoSaveBirchTrigger")));
    R.Run(TEXT("LittlerootTown_EventScript_TownSign"));R.Tick(0);
    TestTrue(TEXT("Original town sign text displayed"),R.Dialogue.Contains(TEXT("LITTLEROOT")));R.AdvanceDialogue();
    FEmeraldEventLabel Bad;Bad.Commands={{TEXT("setvar"),{TEXT("VAR_LITTLEROOT_TOWN_STATE"),TEXT("99")},1},{TEXT("unsupported_fixture_opcode"),{},2}};R.Labels.Add(TEXT("Fixture_Rollback"),Bad);
    R.Run(TEXT("Fixture_Rollback"));R.Tick(0);
    TestEqual(TEXT("Unknown opcode rolls back state transaction"),static_cast<int32>(R.Var(TEXT("VAR_LITTLEROOT_TOWN_STATE"))),1);
    TestTrue(TEXT("Unsupported is explicit"),R.LastError.Contains(TEXT("unsupported_fixture_opcode")));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEmeraldGuardSequence,"Emerald.Events.OriginalGuardSequence",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEmeraldGuardSequence::RunTest(const FString& Parameters)
{
    FEmeraldEventRuntime R;if(!LoadRuntime(R))return false;R.Reset();R.EnterMap(TEXT("MAP_LITTLEROOT_TOWN"),{10,1});R.State.PlayerFacing=2;
    R.Run(R.CoordinateScript({10,1},3));Drive(R);
    TestTrue(TEXT("Original guard program terminates without unsupported actions"),R.LastError.IsEmpty()&&!R.VM.Busy);
    TestEqual(TEXT("Original player pushed one tile back"),R.State.PlayerTile,FIntPoint(10,2));
    TestEqual(TEXT("Original backward push retains north facing"),R.State.PlayerFacing,2);
    TestEqual(TEXT("Original twin returns to guard position"),R.State.Objects[1].Tile,FIntPoint(7,2));
    TestFalse(TEXT("Source unlock restores normal player facing changes"),R.State.PlayerFacingLocked);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEmeraldSourceGait,"Emerald.Events.AuthoredWalkCadence",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEmeraldSourceGait::RunTest(const FString& Parameters)
{
    FEmeraldEventRuntime R;if(!LoadRuntime(R))return false;R.Reset();R.EnterMap(TEXT("MAP_LITTLEROOT_TOWN"),{10,10});
    auto& O=R.State.Objects[2];O.Movement=TEXT("MOVEMENT_TYPE_NONE");const FVector2D Start=O.DrawTile;
    FEmeraldEventLabel Sequence;Sequence.Commands={{TEXT("walk_normal_down"),{},1},{TEXT("delay_8"),{},2},{TEXT("walk_in_place_normal_down"),{},3},{TEXT("step_end"),{},4}};
    R.Labels.Add(TEXT("Fixture_SourceWalkCadence"),Sequence);FString Error;
    TestTrue(TEXT("Start authored movement"),R.StartMovement(2,TEXT("Fixture_SourceWalkCadence"),Error));R.Tick(0);
    TestTrue(TEXT("Normal scripted step exposes walking gait"),R.State.Moves[2].Walking);
    TestTrue(TEXT("Normal step retains original sixteen-frame duration"),FMath::IsNearlyEqual(R.State.Moves[2].Duration,16.f/60.f));
    R.Tick(8.f/60.f);TestTrue(TEXT("Halfway interpolation still source exact"),O.DrawTile.Equals(Start+FVector2D(0,.5),.001));
    R.Tick(8.f/60.f);R.Tick(0);TestFalse(TEXT("Delay does not expose walking gait"),R.State.Moves[2].Walking);
    const FVector2D AtDelay=O.DrawTile;R.Tick(8.f/60.f);R.Tick(0);
    TestTrue(TEXT("In-place walking has a gait without tile displacement"),R.State.Moves[2].Walking);
    TestTrue(TEXT("In-place step remains at its source tile"),R.State.Moves[2].Start.Equals(R.State.Moves[2].End)&&O.DrawTile.Equals(AtDelay));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEmeraldAutonomousMovement,"Emerald.Events.AutonomousWanderAndReservations",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEmeraldAutonomousMovement::RunTest(const FString& Parameters)
{
    FEmeraldEventRuntime A,B;if(!LoadRuntime(A)||!LoadRuntime(B))return false;
    A.Reset();B.Reset();A.EnterMap(TEXT("MAP_LITTLEROOT_TOWN"),{10,10});B.EnterMap(TEXT("MAP_LITTLEROOT_TOWN"),{10,10});
    const auto Home=A.State.Objects[2].Home;int32 Steps=0;bool ReservationChecked=false;
    for(int32 Frame=0;Frame<60*120;++Frame)
    {
        A.TickAutonomous(1.f/60.f);
        const auto& O=A.State.Objects[2];
        if(O.AutonomousMoving)
        {
            TestTrue(TEXT("Source range X respected"),FMath::Abs(O.Tile.X-Home.X)<=O.Range.X);
            TestTrue(TEXT("Source range Y respected"),FMath::Abs(O.Tile.Y-Home.Y)<=O.Range.Y);
            if(!ReservationChecked){TestTrue(TEXT("Both destination and previous tile reserved"),A.ObjectBlocked(O.Tile,3)&&A.ObjectBlocked(O.PreviousTile,3));ReservationChecked=true;}
        }
        Steps=O.AutonomousSteps;
    }
    for(int32 Frame=0;Frame<30*120;++Frame)B.TickAutonomous(1.f/30.f);
    TestTrue(TEXT("Actually took original normal steps"),Steps>10);TestTrue(TEXT("Checked in-flight reservation"),ReservationChecked);
    TestEqual(TEXT("Frame-rate independent source RNG calls"),A.MovementRng,B.MovementRng);
    for(const auto& Pair:A.State.Objects)
    {const auto& Other=B.State.Objects[Pair.Key];TestEqual(TEXT("Frame-rate independent tile"),Pair.Value.Tile,Other.Tile);TestTrue(TEXT("Frame-rate independent draw coordinate"),Pair.Value.DrawTile.Equals(Other.DrawTile));}
    auto& O=A.State.Objects[2];
    TestEqual(TEXT("Reject outside original range"),A.AutonomousCollision(O,Home+FIntPoint(3,0),4),1);
    A.SetObjectTile(2,Home,false);O.Home=Home;O.Range={2,1};A.State.PlayerTile=Home+FIntPoint(1,0);A.State.PlayerPreviousTile=Home+FIntPoint(-1,0);A.State.PlayerMoving=true;
    TestEqual(TEXT("NPC cannot enter player destination"),A.AutonomousCollision(O,A.State.PlayerTile,4),4);
    TestEqual(TEXT("NPC cannot enter player previous reserved tile"),A.AutonomousCollision(O,A.State.PlayerPreviousTile,3),4);
    A.State.PlayerMoving=false;A.State.PlayerTile={10,10};A.VM.Busy=true;
    const auto Before=O.Tile;const uint32 RandomBefore=A.MovementRng;A.TickAutonomous(5.f);
    TestEqual(TEXT("Script lock stops new autonomous decisions"),O.Tile,Before);TestEqual(TEXT("Script lock does not consume movement RNG"),A.MovementRng,RandomBefore);A.VM.Busy=false;
    O.Tile=Home+FIntPoint(1,0);O.PreviousTile=Home;O.DrawTile=FVector2D(Home);O.AutonomousMoving=true;O.AutonomousFrames=0;
    FEmeraldEventLabel Lock;Lock.Commands={{TEXT("lockall"),{},1},{TEXT("setvar"),{TEXT("VAR_0x8000"),TEXT("42")},2},{TEXT("end"),{},3}};A.Labels.Add(TEXT("Fixture_LockSettlement"),Lock);
    A.Run(TEXT("Fixture_LockSettlement"));A.Tick(0);TestTrue(TEXT("Lock waits for in-flight source step"),A.VM.Busy);
    for(int32 I=0;I<20;++I)A.Tick(1.f/60.f);
    TestFalse(TEXT("Lock proceeds after settlement"),A.VM.Busy);TestFalse(TEXT("No half-cell freeze"),O.AutonomousMoving);TestTrue(TEXT("Settled exact source position"),O.DrawTile.Equals(FVector2D(O.Tile)));
    TestEqual(TEXT("Lock command continued original VM"),static_cast<int32>(A.Var(TEXT("VAR_0x8000"))),42);
    return true;
}
#endif

#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

struct FEmeraldEventCommand { FString Op; TArray<FString> Args; int32 Line=0; };
struct FEmeraldEventLabel { FString Next, Source; TArray<FEmeraldEventCommand> Commands; };
struct FEmeraldSourceObject
{
    int32 Id=0, Flag=0, Elevation=0, Facing=1, OriginalFacing=1, Graphics=0;
    FString GraphicsName, Movement, Script;
    FIntPoint Tile, Home, Range;
    FVector2D DrawTile;
    bool Visible=false, FacingLocked=false;
    FIntPoint PreviousTile;
    int32 AutonomousFrames=0, AutonomousDelay=-1, AutonomousSteps=0;
    bool AutonomousMoving=false;
};
struct FEmeraldSourceMove
{
    int32 Id=0, Index=0; FString Label;
    float Elapsed=0, Duration=0;
    bool Walking=false;
    FVector2D Start, End;
};
struct FEmeraldSourceStore
{
    TMap<int32,uint16> Vars;
    TSet<int32> Flags;
    TMap<int32,FEmeraldSourceObject> Objects;
    TMap<FIntPoint,uint16> CellOverrides;
    TMap<int32,FEmeraldSourceMove> Moves;
    TMap<FString,FString> Buffers;
    FString Map, Layout, PlayerName=TEXT("BRENDAN"), RivalName=TEXT("MAY");
    FIntPoint PlayerTile=FIntPoint(10,10), PlayerPreviousTile=FIntPoint(10,10); bool PlayerMoving=false; FVector2D PlayerDraw=FVector2D(10,10);
    int32 Gender=0, PlayerFacing=1, PartyCount=0, Interactor=0, Hour=0, Minute=0;
    bool PlayerHidden=false, PlayerFacingLocked=false;
};
struct FEmeraldSourceCursor { FString Label; int32 Index=0; };

// VM is engine-independent source logic; rendering, sound and special UIs are
// explicit effects. Unknown opcodes fail and roll back the script transaction.
class FEmeraldEventRuntime;
class FEmeraldSourceVM
{
public:
    FEmeraldEventRuntime* Owner=nullptr;
    TArray<FEmeraldSourceCursor> Stack;
    FEmeraldSourceStore Before;
    FString Root, Error, RequestedBefore;
    FIntPoint RequestedTileBefore;
    int32 EffectsBefore=0;
    float Delay=0;
    int32 WaitMove=-1;
    bool Busy=false, WaitingDialogue=false, WaitingClock=false, WaitingWarp=false;
    bool Start(FEmeraldEventRuntime& Runtime,const FString& Label);
    void Pump(float DeltaSeconds, bool bImmediate=false);
    void Fail(const FString& Why);
};

class FEmeraldEventRuntime
{
public:
    TMap<FString,int32> Constants;
    TMap<FString,FEmeraldEventLabel> Labels;
    TMap<FString,FString> Texts;
    TMap<FString,TMap<FString,int32>> LocalIds;
    TMap<FString,TMap<FString,FString>> Callbacks;
    TMap<FString,TSharedPtr<FJsonObject>> Maps;
    TArray<int32> InitialFlags;
    FEmeraldSourceStore State;
    FEmeraldSourceVM VM;
    TSet<FString> Unsupported, EmittedEffectKinds;
    TMap<FString,int32> Executed;
    TArray<FString> Trace;
    TArray<TSharedPtr<FJsonObject>> Effects;
    FString Dialogue, LastError, RequestedMap;
    FIntPoint RequestedTile;
    TArray<FString> Pages;
    int32 Page=0; bool YesNo=false, ClockReadOnly=false, Enabled=true;
    int32 Revision=0;
    TSharedPtr<FJsonObject> MovementContract;
    uint32 MovementRng=0;
    double AutonomousRemainder=0;

    bool Load(const FString& ProgramPath,const TSharedPtr<FJsonObject>& Manifest,FString& Error);
    void Reset(int32 Gender=0,bool bAfterClock=true);
    bool EnterMap(const FString& Id,FIntPoint PlayerTile);
    bool RunImmediate(const FString& Label);
    bool Run(const FString& Label,int32 Interactor=0);
    void Tick(float Seconds);
    void AdvanceDialogue(bool Answer=true);
    void ConfirmClock(int32 Hour,int32 Minute);
    int32 Literal(const FString& Token) const;
    int32 Value(const FString& Token) const;
    uint16 Var(const FString& Name) const;
    void SetVar(const FString& Name,int32 Value);
    bool Flag(const FString& Name) const;
    void SetFlag(const FString& Name,bool Set);
    bool ObjectBlocked(FIntPoint Tile,int32 Elevation) const;
    const FEmeraldSourceObject* ObjectAt(FIntPoint Tile,int32 Elevation) const;
    FString CoordinateScript(FIntPoint Tile,int32 Elevation) const;
    FString BackgroundScript(FIntPoint Tile,int32 Facing,int32 Elevation) const;
    bool StartMovement(int32 Id,const FString& Label,FString& Error);
    bool Special(const FString& Name,const FString& ResultVar,FEmeraldSourceVM& Machine);
    void Emit(const FString& Kind,const TArray<FString>& Args);
    FString FormatText(const FString& Label) const;
    void ShowText(const FString& Label,bool bYesNo);
    int32 FacingFromMovement(const FString& Movement,int32 Fallback) const;
    void SetObjectTile(int32 Id,FIntPoint Tile,bool bPermanent);
    void SetObjectFacing(int32 Id,int32 Facing);
    bool HasMove(int32 Id) const;
    void TickMoves(float Seconds);
    void TickAutonomous(float Seconds);
    int32 AutonomousCollision(const FEmeraldSourceObject& Object,FIntPoint Target,int32 Facing) const;
    bool AutonomousBusy() const;
    uint16 NextMovementRandom();
    bool Callback(const FString& Type,bool Table=false);
    bool IsLocked() const { return VM.Busy || !Dialogue.IsEmpty(); }
};

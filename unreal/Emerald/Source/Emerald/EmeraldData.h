#pragma once
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Dom/JsonObject.h"
#include "EmeraldEvents.h"
#include "EmeraldData.generated.h"

// Elevation is the original movement/collision layer, never an inferred Z height.
struct FEmeraldCell
{
    uint16 SourceWord = 0;
    int32 Metatile = 0, Collision = 0, Elevation = 0, Behavior = 0;
};
struct FEmeraldWarp
{
    FIntPoint Tile;
    FString Destination;
    int32 DestinationIndex = 0;
};
struct FEmeraldMap
{
    FString Id, Name;
    int32 Width = 0, Height = 0;
    TArray<FEmeraldCell> Cells;
    TArray<FEmeraldWarp> Warps;
    TSharedPtr<FJsonObject> Source;
    const FEmeraldCell* Cell(FIntPoint Tile) const;
};

UCLASS()
class EMERALD_API UEmeraldData : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    bool Load(const FString& Path, FString& Error);
    const FEmeraldMap* Map(const FString& Id) const { return Maps.Find(Id); }
    const TMap<FString, FEmeraldMap>& AllMaps() const { return Maps; }
    bool ResolveWarp(const FString& MapId, int32 Index, FString& TargetMap, FIntPoint& TargetTile) const;
    // Static cell gate. Dynamic objects, directional behaviors and scripted gates
    // belong to runtime state; they must not be conflated with this base-grid gate.
    bool CanEnter(const FString& MapId, FIntPoint Tile, int32 FromElevation) const;
    bool bCaptureSweep = false;
    bool bThirdPersonView = false;
    int32 CaptureIndex = 0;
    FString CaptureDirectory;
    TArray<FString> CaptureMapIds;
    bool bSmokeActive = false;
    bool bSmokeStepInFlight = false;
    int32 SmokeIndex = 0;
    TSet<FString> SmokeWarps;
    TArray<TSharedPtr<FJsonValue>> SmokeSteps;
    void FinishSmoke(bool bSuccess, const FString& Message);
    bool bEventSmoke=false;
    int32 EventStage=0;
    float EventSeconds=0, EventStageSeconds=0;
    FKey EventReleaseKey;
    FString EventShotDirectory;
    void FinishEventSmoke(bool bSuccess,const FString& Message);
    TUniquePtr<FEmeraldEventRuntime> Story;
    FString PendingMap;
    FIntPoint PendingTile;
    bool IsReady() const { return Maps.Num() == 6; }
    const TSharedPtr<FJsonObject>& Manifest() const { return Root; }
private:
    TSharedPtr<FJsonObject> Root;
    TMap<FString, FEmeraldMap> Maps;
};

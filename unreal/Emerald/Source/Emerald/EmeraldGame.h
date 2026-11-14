#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "EmeraldGame.generated.h"

class UEmeraldData;
class UCameraComponent;
class USpringArmComponent;
class UStaticMeshComponent;
class AStaticMeshActor;
class AEmeraldFigure;
class FJsonObject;

UCLASS()
class EMERALD_API AEmeraldMapAnchor : public AActor
{
    GENERATED_BODY()
public:
    AEmeraldMapAnchor();
    UPROPERTY(EditAnywhere, Category="Source") FString MapId = TEXT("MAP_LITTLEROOT_TOWN");
};

UCLASS()
class EMERALD_API AEmeraldPawn : public APawn
{
    GENERATED_BODY()
public:
    AEmeraldPawn();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Component) override;
    bool TryStep(FIntPoint Direction);
    FIntPoint GridTile() const { return Tile; }
    FString CurrentMap() const { return MapId; }
    bool CreditsVisible() const {return bCreditsVisible;}
    const TArray<FString>& AssetCredits() const {return CreditsLines;}
private:
    bool bCreditsVisible=false,bCreditsSmokeDone=false;
    int32 CreditsSmokeStage=0;
    TArray<FString> CreditsLines;
    void ToggleCredits();
    void ToggleCamera();
    void ApplyCameraMode(bool ThirdPerson);
    bool bCameraSmokeDone=false;
    int32 CameraSmokeStage=0;
    FIntPoint CameraSmokeTile;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Body;
    UPROPERTY() TObjectPtr<USpringArmComponent> Arm;
    UPROPERTY() TObjectPtr<UCameraComponent> Camera;
    UPROPERTY() TObjectPtr<UEmeraldData> Data;
    FString MapId;
    FIntPoint Tile = FIntPoint(10,10);
    FIntPoint Facing = FIntPoint(0,1);
    int32 Elevation = 3;
    float StepTime = 0, StepDuration = 16.f/60.f;
    float CaptureElapsed = 0;
    int32 GuardFpsCap=60,CaptureMeasuredFrames=0;
    double CaptureWallStart=0;
    bool bScreenshotRequested = false;
    bool bLightingSweep = false;
    bool bQualityViews=false,bQualityGround=false;
    bool bPerspectiveCapture=false;
    int32 LightingIndex = 0;
    int32 PreviewFrameCount=0,PreviewFrameIndex=0;
    float PreviewNextTime=0;
    bool bPreviewFramePending=false;
    TArray<float> LightingGains = {1.f,100.f,1000.f,5000.f};
    void SetCaptureSky(float Intensity);
    bool bMoving = false, bTravel = false, bWarpSuppressed = true;
    FVector StepStart, StepEnd;
    void FinishStep();
    void ReleaseMouse();
    void Interact();
    void Confirm();
    void Cancel();
    void ClockLeft(); void ClockRight(); void ClockUp(); void ClockDown();
    void SyncSourceActors();
    void TickEventSmoke(float Seconds);
    TMap<int32,TWeakObjectPtr<AEmeraldFigure>> SourceActors;
    UPROPERTY() TObjectPtr<AEmeraldFigure> PlayerFigure;
    TSharedPtr<FJsonObject> CharacterRegistry;
    void InitializeCharacters();
    TSharedPtr<FJsonObject> CharacterProfile(const FString& Role) const;
    int32 SelectedHour=0,SelectedMinute=0;
    bool bClockWasOpen=false;
public:
    int32 ClockHour() const {return SelectedHour;}
    int32 ClockMinute() const {return SelectedMinute;}

};

UCLASS()
class EMERALD_API AEmeraldGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AEmeraldGameMode();
};

UCLASS()
class EMERALD_API AEmeraldHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};

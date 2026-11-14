#include "EmeraldGame.h"
#include "EmeraldFigure.h"
#include "Engine/Engine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "EmeraldData.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Components/InputComponent.h"
#include "Engine/StaticMesh.h"
#include "UnrealClient.h"
#include "HAL/FileManager.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/SkyLight.h"
#include "Engine/PostProcessVolume.h"
#include "Components/SkyLightComponent.h"
#include "Components/LightComponent.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "InputKeyEventArgs.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"
#include "Materials/MaterialInterface.h"

namespace
{
FIntPoint DirectionFromSource(int32 D) {if(D==2)return {0,-1};if(D==3)return {-1,0};if(D==4)return {1,0};return {0,1};}
int32 SourceFromDirection(FIntPoint D) {return D.Y<0?2:D.X<0?3:D.X>0?4:1;}
}

AEmeraldMapAnchor::AEmeraldMapAnchor()
{
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("SourceMapAnchor"));
}

AEmeraldPawn::AEmeraldPawn()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("GridRoot"));
    Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DiagnosticPawn"));
    Body->SetupAttachment(RootComponent);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Shape(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    Body->SetStaticMesh(Shape.Object);
    Body->SetRelativeScale3D(FVector(0.6,0.6,1.2));
    Body->SetRelativeLocation(FVector(0,0,60));
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Arm = CreateDefaultSubobject<USpringArmComponent>(TEXT("GameplayCameraArm"));
    Arm->SetupAttachment(RootComponent);
    Arm->TargetArmLength = 2400;
    Arm->SetRelativeRotation(FRotator(-55,-90,0));
    Arm->bDoCollisionTest = false;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("GameplayCamera"));
    Camera->SetupAttachment(Arm);
    Camera->ProjectionMode = ECameraProjectionMode::Orthographic;
    Camera->OrthoWidth = 2600;
    Camera->bAutoCalculateOrthoPlanes = true;
    Camera->bOverrideAspectRatioAxisConstraint = true;
    Camera->SetAspectRatioAxisConstraint(EAspectRatioAxisConstraint::AspectRatio_MaintainXFOV);
}

void AEmeraldPawn::BeginPlay()
{
    Super::BeginPlay();
    CreditsLines={
        TEXT("Canino3d Studio - Free Cartoon Game Man Character (Rigged)"),
        TEXT("CC BY 4.0 - https://creativecommons.org/licenses/by/4.0/"),
        TEXT("https://www.fab.com/listings/d2d871a0-50ea-4041-9889-3f27e5377bb3"),
        TEXT("Models/materials adapted; motion retargeted where used. No endorsement implied."),
        TEXT("crow - Retrofuturistic Computer - CC BY 4.0"),
        TEXT("https://www.fab.com/listings/7304fe63-018f-464f-b7ac-b544ed9285d6"),
        TEXT("Toss - Fridge - CC BY 4.0"),
        TEXT("https://www.fab.com/listings/4c8ac069-4587-4325-a39f-5ab8bf129966"),
        TEXT("Jimbogies - Bathroom Sink Cabinet - CC BY 4.0"),
        TEXT("https://www.fab.com/listings/f9018670-caa2-4fc3-8059-6dbfe0227097"),
        TEXT(""),
        TEXT("giyas3dartist - Cartoon Cute Girl / Cartoon Young Boy - Fab Standard License"),
        TEXT("Quaternius - Character bases and motion - CC0"),
        TEXT("StyleHex Studio - Forest assets - Fab Standard License"),
        TEXT("Tidal Flask Studios - Village parts - Fab Standard License"),
        TEXT("3dShowdown - Modern Staircase Collection - Fab Standard License"),
        TEXT("Quixel Megascans - Door/window/grass/lawn - Fab Standard License"),
        TEXT("Poly Haven contributors - Surfaces and furniture - CC0"),
        TEXT("Epic Games - ArchVis Example tree - Unreal Engine EULA")};
    const FString CapText=FPlatformMisc::GetEnvironmentVariable(TEXT("GPU_SLOT_FPS_CAP"));
    GuardFpsCap=CapText==TEXT("30")?30:60;
    if(IFileManager::Get().FileExists(*(FPlatformProcess::UserHomeDir()+FString(TEXT(".cache/gpu-slot/STREAMING")))))GuardFpsCap=30;
    if(GEngine)GEngine->SetMaxFPS(GuardFpsCap);
    UE_LOG(LogTemp,Display,TEXT("EMERALD_FRAME_CAP requested=%d actual=%.0f"),GuardFpsCap,GEngine?GEngine->GetMaxFPS():0.f);
    Data = GetGameInstance()->GetSubsystem<UEmeraldData>();
    int32 AnchorCount=0;
    for (TActorIterator<AEmeraldMapAnchor> It(GetWorld()); It; ++It)
    { MapId=It->MapId; ++AnchorCount; }
    const auto* M = Data ? Data->Map(MapId) : nullptr;
    if (!M || AnchorCount!=1) { UE_LOG(LogTemp, Error, TEXT("EMERALD_GAME no source map anchor/data")); SetActorTickEnabled(false); return; }
    if (Data->PendingMap == MapId)
    {
        Tile=Data->PendingTile;
        Data->PendingMap.Empty();
        // Door exits place the actor one tile south, as the source warp-exit
        // movement does. Stairs retain their exact destination warp tile.
        const auto* C=M->Cell(Tile);
        if (C && C->Behavior==0x69 && Data->CanEnter(MapId,Tile+FIntPoint(0,1),0)) Tile+=FIntPoint(0,1);
    }
    else
    {
        Tile=MapId==TEXT("MAP_LITTLEROOT_TOWN") ? FIntPoint(10,10) : FIntPoint(M->Width/2,M->Height-3);
    }
    if (const auto* C=M->Cell(Tile)) Elevation=C->Elevation;
    SetActorLocation(FVector(Tile.X*200,Tile.Y*200,0));
    if(Data->bCaptureSweep && Data->Story && (FParse::Param(FCommandLine::Get(),TEXT("EmeraldCaptureWander")) || FParse::Param(FCommandLine::Get(),TEXT("EmeraldCapturePerspective"))))
    {
        Data->Story->Reset(Data->Story->State.Gender,true);
        UE_LOG(LogTemp,Display,TEXT("EMERALD_CAPTURE_SOURCE_RESET map=%s gender=%d fixture=post-clock"),*MapId,Data->Story->State.Gender);
    }
    InitializeCharacters();
    if(Data->Story && Data->Story->Enabled)
    {
        if(Data->bEventSmoke){Tile={14,13};Facing={1,0};SetActorLocation(FVector(2800,2600,0));}
        if(!Data->Story->EnterMap(MapId,Tile))UE_LOG(LogTemp,Error,TEXT("EMERALD_SOURCE_MAP_FAILED map=%s reason=%s"),*MapId,*Data->Story->LastError);
        SyncSourceActors();
    }
    if(Data->bCaptureSweep)
    {
        bLightingSweep=FParse::Param(FCommandLine::Get(),TEXT("EmeraldLightingSweep"));
        if(FParse::Value(FCommandLine::Get(),TEXT("EmeraldPreviewFrames="),PreviewFrameCount))
        {
            if(!bLightingSweep || !GetWorld()->GetOutermost()->GetName().StartsWith(TEXT("/Game/QualityGallery/")) || PreviewFrameCount<1 || PreviewFrameCount>120)
            {UE_LOG(LogTemp,Error,TEXT("Preview frames require an owned gallery and1..120frames"));bTravel=true;FPlatformMisc::RequestExitWithStatus(false,1);return;}
        }
        bQualityViews=FParse::Param(FCommandLine::Get(),TEXT("EmeraldQualityViews"));
        bPerspectiveCapture=FParse::Param(FCommandLine::Get(),TEXT("EmeraldCapturePerspective"));
        Body->SetVisibility(false);
        if(PlayerFigure)PlayerFigure->SetSourceVisible(false);
        // Fit the actual sourced scene, including wall-mounted fixtures and
        // tree crowns. Floor dimensions alone clip tall props at the top.
        const FRotationMatrix Axes(Arm->GetComponentRotation());
        const FVector Right=Axes.GetUnitAxis(EAxis::Y),Up=Axes.GetUnitAxis(EAxis::Z);
        double MinX=DBL_MAX,MinY=DBL_MAX,MaxX=-DBL_MAX,MaxY=-DBL_MAX;
        int32 Fitted=0;
        for(TActorIterator<AStaticMeshActor> It(GetWorld());It;++It)
        {
            if(!It->ActorHasTag(TEXT("EmeraldGenerated")) || It->ActorHasTag(TEXT("EmeraldBackdrop")))continue;
            const FBox Bounds=It->GetComponentsBoundingBox(true);
            if(!Bounds.IsValid)continue;
            ++Fitted;
            for(int32 I=0;I<8;++I)
            {
                const FVector P(I&1?Bounds.Max.X:Bounds.Min.X,I&2?Bounds.Max.Y:Bounds.Min.Y,I&4?Bounds.Max.Z:Bounds.Min.Z);
                const double X=FVector::DotProduct(P,Right),Y=FVector::DotProduct(P,Up);
                MinX=FMath::Min(MinX,X);MaxX=FMath::Max(MaxX,X);
                MinY=FMath::Min(MinY,Y);MaxY=FMath::Max(MaxY,Y);
            }
        }
        FVector Target((M->Width-1)*100,(M->Height-1)*100,0);
        FVector2D ViewportSize(1280,800);
        if(GEngine && GEngine->GameViewport)GEngine->GameViewport->GetViewportSize(ViewportSize);
        const double Aspect=ViewportSize.X>0 && ViewportSize.Y>0?ViewportSize.X/ViewportSize.Y:1.6;
        if(Fitted)
        {
            Target+=Right*((MinX+MaxX)*.5-FVector::DotProduct(Target,Right));
            Target+=Up*((MinY+MaxY)*.5-FVector::DotProduct(Target,Up));
            Camera->OrthoWidth=FMath::Max(MaxX-MinX,(MaxY-MinY)*Aspect)*1.08;
        }
        if(bQualityViews)
        {
            FString LockPath,LockText;TSharedPtr<FJsonObject> Lock;
            if(FParse::Value(FCommandLine::Get(),TEXT("EmeraldQualityCameraLock="),LockPath) && FFileHelper::LoadFileToString(LockText,*LockPath) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(LockText),Lock) && Lock.IsValid() && Lock->HasField(MapId))
            {const auto P=Lock->GetObjectField(MapId);const auto& V=P->GetArrayField(TEXT("target"));Target=FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber());Camera->OrthoWidth=P->GetNumberField(TEXT("ortho_width_cm"));}
            UE_LOG(LogTemp,Display,TEXT("EMERALD_QUALITY_OVERHEAD map=%s target=%.4f,%.4f,%.4f width=%.4f"),*MapId,Target.X,Target.Y,Target.Z,Camera->OrthoWidth);
        }
        SetActorLocation(Target);
        Arm->TargetArmLength=8000;
        if(bLightingSweep)
        {
            FString Values;
            if(FParse::Value(FCommandLine::Get(),TEXT("EmeraldSkyGains="),Values,false))
            {
                TArray<FString> Parts;Values.ParseIntoArray(Parts,TEXT(","),true);LightingGains.Reset();
                for(const FString& Part:Parts)
                {
                    const float Gain=FCString::Atof(*Part);
                    if(!Part.IsNumeric() || !FMath::IsFinite(Gain) || Gain<=0 || Gain>100000 || LightingGains.Contains(Gain))
                    {UE_LOG(LogTemp,Error,TEXT("Invalid or repeated sky gain"));bTravel=true;FPlatformMisc::RequestExitWithStatus(false,1);return;}
                    LightingGains.Add(Gain);
                }
                if(LightingGains.IsEmpty() || LightingGains.Num()>8)
                {UE_LOG(LogTemp,Error,TEXT("Expected one to eight sky gains"));bTravel=true;FPlatformMisc::RequestExitWithStatus(false,1);return;}
            }
            SetCaptureSky(LightingGains[0]);
        }
        UE_LOG(LogTemp,Display,TEXT("EMERALD_CAPTURE_FIT map=%s props=%d width=%.2f aspect=%.3f"),*MapId,Fitted,Camera->OrthoWidth,Aspect);
        if(bPerspectiveCapture)
        {
            // Capture-only pose on a real walkable source tile; never move
            // canonical events or introduce a new gameplay spawn/warp.
            const FIntPoint Center(M->Width/2,FParse::Param(FCommandLine::Get(),TEXT("EmeraldCaptureCameraEdges"))?M->Height-2:M->Height/2);int32 Best=MAX_int32;
            for(int32 Y=1;Y<M->Height-1;++Y)for(int32 X=1;X<M->Width-1;++X)
            {
                const FIntPoint Candidate(X,Y);const auto* Cell=M->Cell(Candidate);
                if(!Cell || Cell->Collision)continue;
                bool Occupied=false;
                for(const auto& Warp:M->Warps)if(Warp.Tile==Candidate)Occupied=true;
                if(Data->Story)for(const auto& Pair:Data->Story->State.Objects)if(Pair.Value.Visible&&Pair.Value.Tile==Candidate)Occupied=true;
                const int32 Score=FMath::Abs(X-Center.X)+FMath::Abs(Y-Center.Y);
                if(!Occupied&&Score<Best){Tile=Candidate;Best=Score;}
            }
            if(Best==MAX_int32){UE_LOG(LogTemp,Error,TEXT("EMERALD_PERSPECTIVE_NO_SOURCE_FLOOR"));FPlatformMisc::RequestExitWithStatus(false,1);return;}
            Facing={0,-1};Elevation=M->Cell(Tile)->Elevation;SetActorLocation(FVector(Tile.X*200,Tile.Y*200,0));
            if(Data->Story){Data->Story->State.PlayerTile=Tile;Data->Story->State.PlayerDraw=FVector2D(Tile);Data->Story->State.PlayerFacing=2;}
            if(PlayerFigure){PlayerFigure->SetSourceFacing(2);PlayerFigure->SetSourceVisible(true);}
            Body->SetVisibility(!PlayerFigure||!PlayerFigure->IsReady());ApplyCameraMode(true);
            UE_LOG(LogTemp,Display,TEXT("EMERALD_PERSPECTIVE_POSE map=%s tile=%d,%d collision=%d"),*MapId,Tile.X,Tile.Y,M->Cell(Tile)->Collision);
        }
    }
    if(!Data->bCaptureSweep){Data->bThirdPersonView|=FParse::Param(FCommandLine::Get(),TEXT("EmeraldThirdPerson"));ApplyCameraMode(Data->bThirdPersonView);}
    UE_LOG(LogTemp, Display,TEXT("EMERALD_GAME ready map=%s tile=%d,%d"),*MapId,Tile.X,Tile.Y);
    if(auto* PC=Cast<APlayerController>(GetController()))
    {
        PC->bShowMouseCursor=true;
        PC->SetInputMode(FInputModeGameAndUI().SetHideCursorDuringCapture(false));
    }
}

void AEmeraldPawn::SetCaptureSky(float Intensity)
{
    int32 Count=0;
    for(TActorIterator<ASkyLight> It(GetWorld());It;++It)
    {
        auto* Light=It->GetLightComponent();Light->SetIntensity(Intensity);++Count;
        UE_LOG(LogTemp,Display,TEXT("EMERALD_LIGHTING_SAMPLE requested=%.0f actual=%.0f"),Intensity,Light->Intensity);
    }
    UE_LOG(LogTemp,Display,TEXT("EMERALD_LIGHTING_ACTORS count=%d"),Count);
}

void AEmeraldPawn::SetupPlayerInputComponent(UInputComponent* Component)
{
    Super::SetupPlayerInputComponent(Component);
    Component->BindKey(EKeys::Escape,IE_Pressed,this,&AEmeraldPawn::Cancel);
    Component->BindKey(EKeys::C,IE_Pressed,this,&AEmeraldPawn::ToggleCredits);
    Component->BindKey(EKeys::V,IE_Pressed,this,&AEmeraldPawn::ToggleCamera);
    Component->BindKey(EKeys::E,IE_Pressed,this,&AEmeraldPawn::Confirm);
    Component->BindKey(EKeys::Enter,IE_Pressed,this,&AEmeraldPawn::Confirm);
    Component->BindKey(EKeys::SpaceBar,IE_Pressed,this,&AEmeraldPawn::Confirm);
    Component->BindKey(EKeys::Gamepad_FaceButton_Bottom,IE_Pressed,this,&AEmeraldPawn::Confirm);
    Component->BindKey(EKeys::Gamepad_FaceButton_Right,IE_Pressed,this,&AEmeraldPawn::Cancel);
    Component->BindKey(EKeys::Left,IE_Pressed,this,&AEmeraldPawn::ClockLeft);
    Component->BindKey(EKeys::Right,IE_Pressed,this,&AEmeraldPawn::ClockRight);
    Component->BindKey(EKeys::Up,IE_Pressed,this,&AEmeraldPawn::ClockUp);
    Component->BindKey(EKeys::Down,IE_Pressed,this,&AEmeraldPawn::ClockDown);
}

void AEmeraldPawn::ApplyCameraMode(bool ThirdPerson)
{
    Camera->ProjectionMode=ThirdPerson?ECameraProjectionMode::Perspective:ECameraProjectionMode::Orthographic;
    Camera->FieldOfView=65;Camera->OrthoWidth=2600;
    Arm->TargetArmLength=ThirdPerson?750:2400;
    Arm->SetRelativeRotation(ThirdPerson?FRotator(-12,-90,0):FRotator(-55,-90,0));
    // Keep the inspected unobstructed pose exactly, while tracing from the
    // player's upper body rather than sweeping a camera ray from the feet.
    Arm->TargetOffset=ThirdPerson?Arm->GetComponentRotation().RotateVector(FVector(0,0,235)):FVector::ZeroVector;
    Arm->SocketOffset=ThirdPerson?FVector(0,60,0):FVector::ZeroVector;
    Arm->bDoCollisionTest=ThirdPerson&&MapId!=TEXT("MAP_LITTLEROOT_TOWN");Arm->ProbeSize=4;
    int32 Shown=0,Hidden=0,LocalLights=0;
    for(TActorIterator<AActor> It(GetWorld());It;++It)
    {
        if(It->ActorHasTag(TEXT("EmeraldThirdPersonOnly"))||It->ActorHasTag(TEXT("EmeraldOverheadOnly")))
        {
            const bool Show=It->ActorHasTag(TEXT("EmeraldThirdPersonOnly"))?ThirdPerson:!ThirdPerson;
            It->SetActorHiddenInGame(!Show);Show?++Shown:++Hidden;
            if(auto* Light=It->FindComponentByClass<ULightComponent>()){Light->SetVisibility(Show);++LocalLights;}
        }
    }
    UE_LOG(LogTemp,Display,TEXT("EMERALD_ROOM_VIEW map=%s perspective=%d shown=%d hidden=%d local_lights=%d"),*MapId,ThirdPerson,Shown,Hidden,LocalLights);
    for(TActorIterator<APostProcessVolume> It(GetWorld());It;++It)
    {
        It->Settings.bOverride_AutoExposureBias=true;
        It->Settings.AutoExposureBias=ThirdPerson&&MapId!=TEXT("MAP_LITTLEROOT_TOWN")?3.f:0.f;
        UE_LOG(LogTemp,Display,TEXT("EMERALD_ROOM_EXPOSURE map=%s perspective=%d bias=%.2f"),*MapId,ThirdPerson,It->Settings.AutoExposureBias);
    }
}

void AEmeraldPawn::ToggleCamera()
{
    if(!Data||Data->bCaptureSweep||bCreditsVisible)return;
    Data->bThirdPersonView=!Data->bThirdPersonView;ApplyCameraMode(Data->bThirdPersonView);
    UE_LOG(LogTemp,Display,TEXT("EMERALD_CAMERA_INPUT perspective=%d projection=%d tile=%d,%d"),Data->bThirdPersonView,static_cast<int32>(Camera->ProjectionMode),Tile.X,Tile.Y);
}

void AEmeraldPawn::ReleaseMouse()
{
    if(auto* PC=Cast<APlayerController>(GetController()))
    { PC->bShowMouseCursor=true; PC->SetInputMode(FInputModeGameAndUI().SetHideCursorDuringCapture(false)); }
}

void AEmeraldPawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if(bTravel || !Data) return;
    if(Data->bEventSmoke)TickEventSmoke(DeltaSeconds);
    if(Data->bCaptureSweep)
    {
        if(FParse::Param(FCommandLine::Get(),TEXT("EmeraldCaptureWander")) && Data->Story && Data->Story->Enabled)
        {Data->Story->Tick(DeltaSeconds);SyncSourceActors();}
        if(CaptureElapsed>=2.f)
        {
            if(CaptureWallStart==0)CaptureWallStart=FPlatformTime::Seconds();
            ++CaptureMeasuredFrames;
        }
        CaptureElapsed+=DeltaSeconds;
        if(PreviewFrameCount>0)
        {
            const FString PreviewShot=Data->CaptureDirectory/FString::Printf(TEXT("Motion_%04d.png"),PreviewFrameIndex);
            if(bPreviewFramePending && IFileManager::Get().FileSize(*PreviewShot)>0)
            {
                bPreviewFramePending=false;++PreviewFrameIndex;
                if(PreviewFrameIndex>=PreviewFrameCount){UE_LOG(LogTemp,Display,TEXT("EMERALD_PREVIEW_COMPLETE frames=%d"),PreviewFrameIndex);bTravel=true;FPlatformMisc::RequestExitWithStatus(false,0);return;}
            }
            if(!bPreviewFramePending && CaptureElapsed>3.f && CaptureElapsed>=PreviewNextTime)
            {
                const FString NextShot=Data->CaptureDirectory/FString::Printf(TEXT("Motion_%04d.png"),PreviewFrameIndex);
                FScreenshotRequest::RequestScreenshot(NextShot,false,false);bPreviewFramePending=true;PreviewNextTime=CaptureElapsed+1.f/12.f;
                UE_LOG(LogTemp,Display,TEXT("EMERALD_PREVIEW_FRAME index=%d time_s=%.6f"),PreviewFrameIndex,CaptureElapsed);
            }
            return;
        }
        const auto* M=Data->Map(MapId);
        const FString ViewName=bPerspectiveCapture?TEXT("Perspective_")+M->Name:bQualityViews && MapId==TEXT("MAP_LITTLEROOT_TOWN")?(bQualityGround?TEXT("TownThirdPerson"):TEXT("TownOverhead")):M->Name;
        const FString Shot=Data->CaptureDirectory/(bLightingSweep?FString::Printf(TEXT("Sky_%.0f.png"),LightingGains[LightingIndex]):ViewName+TEXT(".png"));
        if(CaptureElapsed>3.0f && !bScreenshotRequested)
        {
            if(bQualityViews)UE_LOG(LogTemp,Display,TEXT("EMERALD_QUALITY_VIEW name=%s projection=%d fov=%.2f width=%.2f camera=%s rotation=%s"),*ViewName,static_cast<int32>(Camera->ProjectionMode),Camera->FieldOfView,Camera->OrthoWidth,*Camera->GetComponentLocation().ToString(),*Camera->GetComponentRotation().ToString());
            if(bPerspectiveCapture)UE_LOG(LogTemp,Display,TEXT("EMERALD_PERSPECTIVE_VIEW map=%s projection=%d fov=%.2f camera=%s rotation=%s"),*MapId,static_cast<int32>(Camera->ProjectionMode),Camera->FieldOfView,*Camera->GetComponentLocation().ToString(),*Camera->GetComponentRotation().ToString());
            if(bPerspectiveCapture&&FParse::Param(FCommandLine::Get(),TEXT("EmeraldCaptureCameraEdges")))
            {
                const FVector P=Camera->GetComponentLocation();const bool Inside=MapId==TEXT("MAP_LITTLEROOT_TOWN")||(P.X>-100&&P.X<M->Width*200-100&&P.Y>-100&&P.Y<M->Height*200-100&&P.Z>0&&P.Z<500);
                UE_LOG(LogTemp,Display,TEXT("EMERALD_CAMERA_BOUNDARY map=%s inside=%d camera=%s"),*MapId,Inside,*P.ToString());
                if(!Inside){UE_LOG(LogTemp,Error,TEXT("EMERALD_CAMERA_BOUNDARY_FAILED"));FPlatformMisc::RequestExitWithStatus(false,1);return;}
            }
            FScreenshotRequest::RequestScreenshot(Shot,false,false);
            bScreenshotRequested=true;
        }
        if(bScreenshotRequested && CaptureElapsed>4.0f && IFileManager::Get().FileSize(*Shot)>0)
        {
            const double CaptureWall=FPlatformTime::Seconds()-CaptureWallStart;
            UE_LOG(LogTemp,Display,TEXT("EMERALD_CAPTURE_CADENCE map=%s frames=%d wall_s=%.4f fps=%.2f cap=%d"),*MapId,CaptureMeasuredFrames,CaptureWall,CaptureWall>0?CaptureMeasuredFrames/CaptureWall:0,GuardFpsCap);
            UE_LOG(LogTemp,Display,TEXT("EMERALD_CAPTURE saved %s"),*Shot);
            if(bLightingSweep)
            {
                ++LightingIndex;
                if(LightingIndex>=LightingGains.Num()){bTravel=true;FPlatformMisc::RequestExitWithStatus(false,0);return;}
                SetCaptureSky(LightingGains[LightingIndex]);CaptureElapsed=0;bScreenshotRequested=false;return;
            }
            if(bQualityViews && MapId==TEXT("MAP_LITTLEROOT_TOWN") && !bQualityGround)
            {
                bQualityGround=true;Tile={14,13};Facing={0,-1};SetActorLocation(FVector(Tile.X*200,Tile.Y*200,0));
                if(Data->Story){Data->Story->State.PlayerTile=Tile;Data->Story->State.PlayerDraw=FVector2D(Tile);Data->Story->State.PlayerFacing=2;}
                if(PlayerFigure){PlayerFigure->SetSourceFacing(2);PlayerFigure->SetSourceVisible(true);}
                Body->SetVisibility(!PlayerFigure||!PlayerFigure->IsReady());
                Camera->ProjectionMode=ECameraProjectionMode::Perspective;Camera->FieldOfView=65;
                Arm->TargetArmLength=750;Arm->SocketOffset=FVector(0,60,235);Arm->SetRelativeRotation(FRotator(-12,-90,0));
                CaptureElapsed=0;CaptureMeasuredFrames=0;CaptureWallStart=0;bScreenshotRequested=false;return;
            }
            ++Data->CaptureIndex;
            if(Data->CaptureIndex>=Data->CaptureMapIds.Num())
            { FPlatformMisc::RequestExitWithStatus(false,0); return; }
            bTravel=true;
            const auto* Next=Data->Map(Data->CaptureMapIds[Data->CaptureIndex]);
            UGameplayStatics::OpenLevel(this,FName(*(TEXT("/Game/Maps/")+Next->Name)));
        }
        return;
    }
    if(Data->Story && Data->Story->Enabled)
    {
        auto& Story=*Data->Story;
        const bool WasLocked=Story.IsLocked();
        Story.Tick(DeltaSeconds);SyncSourceActors();
        if(!Story.RequestedMap.IsEmpty())
        {
            const auto* Target=Data->Map(Story.RequestedMap);
            if(Target)
            {
                Data->PendingMap=Story.RequestedMap;Data->PendingTile=Story.RequestedTile;Story.RequestedMap.Empty();bTravel=true;
                UGameplayStatics::OpenLevel(this,FName(*(TEXT("/Game/Maps/")+Target->Name)));return;
            }
        }
        if(Story.VM.WaitingClock && !bClockWasOpen){SelectedHour=Story.State.Hour;SelectedMinute=Story.State.Minute;}
        bClockWasOpen=Story.VM.WaitingClock;
        if(WasLocked||Story.IsLocked())
        {
            Tile=Story.State.PlayerTile;Facing=DirectionFromSource(Story.State.PlayerFacing);
            SetActorLocation(FVector(Story.State.PlayerDraw.X*200,Story.State.PlayerDraw.Y*200,0));return;
        }
    }
    if(bMoving)
    {
        StepTime+=DeltaSeconds;
        SetActorLocation(FMath::Lerp(StepStart,StepEnd,FMath::Clamp(StepTime/StepDuration,0.f,1.f)));
        if(StepTime>=StepDuration) FinishStep();
        return;
    }
    if(Data->bSmokeActive)
    {
        if(Data->bSmokeStepInFlight)
        {
            const auto Step=Data->SmokeSteps[Data->SmokeIndex]->AsObject();
            const auto& Expected=Step->GetArrayField(TEXT("expect_tile"));
            const FIntPoint ExpectedTile(Expected[0]->AsNumber(),Expected[1]->AsNumber());
            if(MapId!=Step->GetStringField(TEXT("expect_map")) || Tile!=ExpectedTile)
            { Data->FinishSmoke(false,FString::Printf(TEXT("Step %d arrived at %s %d,%d"),Data->SmokeIndex,*MapId,Tile.X,Tile.Y)); return; }
            ++Data->SmokeIndex;
            Data->bSmokeStepInFlight=false;
        }
        if(Data->SmokeIndex>=Data->SmokeSteps.Num())
        { Data->FinishSmoke(true,TEXT("All planned inputs and 13 source warp links traversed")); return; }
        const auto Step=Data->SmokeSteps[Data->SmokeIndex]->AsObject();
        const auto& From=Step->GetArrayField(TEXT("from_tile"));
        if(MapId!=Step->GetStringField(TEXT("from_map")) || Tile!=FIntPoint(From[0]->AsNumber(),From[1]->AsNumber()))
        { Data->FinishSmoke(false,TEXT("Input scenario starting state mismatch")); return; }
        const auto& Direction=Step->GetArrayField(TEXT("direction"));
        if(!TryStep(FIntPoint(Direction[0]->AsNumber(),Direction[1]->AsNumber())))
        { Data->FinishSmoke(false,FString::Printf(TEXT("Input %d was blocked"),Data->SmokeIndex)); return; }
        Data->bSmokeStepInFlight=true;
        return;
    }
    const auto* PC=Cast<APlayerController>(GetController());
    if(!PC) return;
    if(PC->IsInputKeyDown(EKeys::W)||PC->IsInputKeyDown(EKeys::Up)) TryStep({0,-1});
    else if(PC->IsInputKeyDown(EKeys::S)||PC->IsInputKeyDown(EKeys::Down)) TryStep({0,1});
    else if(PC->IsInputKeyDown(EKeys::A)||PC->IsInputKeyDown(EKeys::Left)) TryStep({-1,0});
    else if(PC->IsInputKeyDown(EKeys::D)||PC->IsInputKeyDown(EKeys::Right)) TryStep({1,0});
}

bool AEmeraldPawn::TryStep(FIntPoint Direction)
{
    if(bCreditsVisible||bMoving||bTravel||!Data||FMath::Abs(Direction.X)+FMath::Abs(Direction.Y)!=1) return false;
    Facing=Direction;
    if(PlayerFigure)PlayerFigure->SetSourceFacing(SourceFromDirection(Facing));
    if(Data->Story && Data->Story->Enabled)
    {
        auto& Story=*Data->Story;Story.State.PlayerFacing=SourceFromDirection(Facing);
        if(Story.IsLocked() || Story.ObjectBlocked(Tile+Direction,Elevation))return false;
    }
    const auto* M=Data->Map(MapId);
    const auto* C=M?M->Cell(Tile+Direction):nullptr;
    if(!C) return false;
    bool bDoor=false;
    for(const auto& W:M->Warps)
        if(W.Tile==Tile+Direction && C->Behavior==0x69 && Direction==FIntPoint(0,-1)) bDoor=true;
    // Source animated doors have collision=1, and are entered by the northward
    // door interaction path, not by the ordinary collision-free walking path.
    bool CanEnter=Data->CanEnter(MapId,Tile+Direction,Elevation);
    if(Data->Story && Data->Story->Enabled)
        if(const auto* Override=Data->Story->State.CellOverrides.Find(Tile+Direction))CanEnter=((*Override&0xC00)==0);
    if(!bDoor&&!CanEnter) return false;
    StepStart=GetActorLocation();
    if(Data->Story && Data->Story->Enabled){Data->Story->State.PlayerPreviousTile=Tile;Data->Story->State.PlayerMoving=true;}
    Tile+=Direction;
    StepEnd=FVector(Tile.X*200,Tile.Y*200,0);
    StepTime=0; bMoving=true;
    if(C->Elevation!=0 && C->Elevation!=15) Elevation=C->Elevation;
    bWarpSuppressed=false;
    if(Data->Story && Data->Story->Enabled)Data->Story->State.PlayerTile=Tile;
    return true;
}

void AEmeraldPawn::FinishStep()
{
    bMoving=false;
    if(Data->Story){Data->Story->State.PlayerMoving=false;Data->Story->State.PlayerPreviousTile=Tile;}
    SetActorLocation(StepEnd);
    const auto* M=Data->Map(MapId);
    if(!M || bWarpSuppressed) return;
    const auto* C=M->Cell(Tile);
    for(int32 I=0;I<M->Warps.Num();++I)
    {
        if(M->Warps[I].Tile!=Tile) continue;
        if(C && C->Behavior==0x65 && Facing!=FIntPoint(0,1)) continue;
        FString Target; FIntPoint Arrival;
        if(!Data->ResolveWarp(MapId,I,Target,Arrival)) return;
        if(Data->bSmokeActive) Data->SmokeWarps.Add(MapId+TEXT(":")+FString::FromInt(I));
        Data->PendingMap=Target; Data->PendingTile=Arrival;
        bTravel=true;
        UE_LOG(LogTemp,Display,TEXT("EMERALD_WARP %s[%d] -> %s tile=%d,%d"),*MapId,I,*Target,Arrival.X,Arrival.Y);
        // A frame-driven fade/black hold will replace this first traversal bridge.
        UGameplayStatics::OpenLevel(this,FName(*(TEXT("/Game/Maps/")+Data->Map(Target)->Name)));
        return;
    }
    if(Data->Story && Data->Story->Enabled)
    {
        auto& Story=*Data->Story;Story.State.PlayerTile=Tile;Story.State.PlayerDraw=FVector2D(Tile);
        const FString Script=Story.CoordinateScript(Tile,Elevation);if(!Script.IsEmpty())Story.Run(Script);
    }
}

void AEmeraldPawn::Interact()
{
    if(!Data||!Data->Story||!Data->Story->Enabled)return;
    auto& Story=*Data->Story;if(Story.IsLocked()||bMoving)return;
    Story.State.PlayerTile=Tile;Story.State.PlayerDraw=FVector2D(Tile);Story.State.PlayerFacing=SourceFromDirection(Facing);
    if(const auto* O=Story.ObjectAt(Tile+Facing,Elevation))
    {
        if(O->Script!=TEXT("0x0")&&O->Script!=TEXT("0"))Story.Run(O->Script,O->Id);
        return;
    }
    const FString Script=Story.BackgroundScript(Tile+Facing,Story.State.PlayerFacing,Elevation);
    if(!Script.IsEmpty())Story.Run(Script);
}
void AEmeraldPawn::Confirm()
{
    if(bCreditsVisible)return;
    if(Data&&Data->Story&&Data->Story->Enabled)
    {
        auto& S=*Data->Story;
        if(S.VM.WaitingClock){S.ConfirmClock(SelectedHour,SelectedMinute);return;}
        if(S.VM.WaitingDialogue){S.AdvanceDialogue(true);return;}
    }
    Interact();
}
void AEmeraldPawn::Cancel()
{
    ReleaseMouse();
    if(bCreditsVisible){bCreditsVisible=false;return;}
    if(Data&&Data->Story)
    {
        auto& S=*Data->Story;
        if(S.VM.WaitingClock&&S.ClockReadOnly)S.ConfirmClock(SelectedHour,SelectedMinute);
        else if(S.VM.WaitingDialogue)S.AdvanceDialogue(false);
    }
}
void AEmeraldPawn::ToggleCredits(){bCreditsVisible=!bCreditsVisible;}
void AEmeraldPawn::ClockLeft(){if(!bCreditsVisible&&Data&&Data->Story&&Data->Story->VM.WaitingClock&&!Data->Story->ClockReadOnly)SelectedMinute=(SelectedMinute+59)%60;}
void AEmeraldPawn::ClockRight(){if(!bCreditsVisible&&Data&&Data->Story&&Data->Story->VM.WaitingClock&&!Data->Story->ClockReadOnly)SelectedMinute=(SelectedMinute+1)%60;}
void AEmeraldPawn::ClockUp(){if(!bCreditsVisible&&Data&&Data->Story&&Data->Story->VM.WaitingClock&&!Data->Story->ClockReadOnly)SelectedHour=(SelectedHour+1)%24;}
void AEmeraldPawn::ClockDown(){if(!bCreditsVisible&&Data&&Data->Story&&Data->Story->VM.WaitingClock&&!Data->Story->ClockReadOnly)SelectedHour=(SelectedHour+23)%24;}

TSharedPtr<FJsonObject> AEmeraldPawn::CharacterProfile(const FString& Role) const
{
    if(!CharacterRegistry.IsValid() || !CharacterRegistry->GetObjectField(TEXT("profiles"))->HasField(Role))return nullptr;
    return CharacterRegistry->GetObjectField(TEXT("profiles"))->GetObjectField(Role);
}

void AEmeraldPawn::InitializeCharacters()
{
    if(!Data || !Data->Story || !Data->Story->Enabled)return;
    FString Text;
    if(!FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Imported/Data/character-assets.json"))) ||
       !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),CharacterRegistry) ||
       !CharacterRegistry.IsValid() || !CharacterRegistry->HasField(TEXT("schema")) || CharacterRegistry->GetStringField(TEXT("schema"))!=TEXT("emerald.character-profiles/1"))
    {UE_LOG(LogTemp,Error,TEXT("EMERALD_CHARACTER_REGISTRY_MISSING"));CharacterRegistry.Reset();return;}
    const FString Role=Data->Story->State.Gender==0?TEXT("player_male"):TEXT("player_female");
    PlayerFigure=GetWorld()->SpawnActor<AEmeraldFigure>();
    PlayerFigure->AttachToActor(this,FAttachmentTransformRules::KeepRelativeTransform);
    PlayerFigure->AddTickPrerequisiteActor(this);PlayerFigure->Configure(Role,CharacterProfile(Role));
    PlayerFigure->SetSourceFacing(SourceFromDirection(Facing));PlayerFigure->SetSourceVisible(!Data->bCaptureSweep);
    if(PlayerFigure->IsReady())Body->SetVisibility(false);
}

void AEmeraldPawn::SyncSourceActors()
{
    if(!Data||!Data->Story)return;
    auto& State=Data->Story->State;int32 Expected=0,Rendered=0,Diagnostics=0;
    const auto Graphics=CharacterRegistry.IsValid()?CharacterRegistry->GetObjectField(TEXT("graphics")):nullptr;
    for(const auto& Pair:State.Objects)
    {
        const auto& O=Pair.Value;auto* A=SourceActors.FindRef(O.Id).Get();
        if(!A && !O.Visible)continue;
        FString Role;
        if(Graphics.IsValid())Graphics->TryGetStringField(FString::FromInt(O.Graphics),Role);
        const auto Profile=CharacterProfile(Role);
        if(!A)
        {
            A=GetWorld()->SpawnActor<AEmeraldFigure>();A->AddTickPrerequisiteActor(this);SourceActors.Add(O.Id,A);
        }
        A->Configure(Role.IsEmpty()?TEXT("diagnostic_")+FString::FromInt(O.Graphics):Role,Profile);
        A->SetActorLocation(FVector(O.DrawTile.X*200,O.DrawTile.Y*200,0));A->SetSourceFacing(O.Facing);
        const auto* SourceMap=Data->Map(MapId);const auto* Cell=SourceMap?SourceMap->Cell(O.Tile):nullptr;
        const bool Chair=Cell && (MapId.Contains(TEXT("HOUSE_1F"))?(Cell->Metatile==0x219||Cell->Metatile==0x221||Cell->Metatile==0x2C0||Cell->Metatile==0x21C||Cell->Metatile==0x224||Cell->Metatile==0x2C3):(MapId.Contains(TEXT("BIRCHS_LAB"))&&(Cell->Metatile==0x239||Cell->Metatile==0x249||Cell->Metatile==0x241)));
        const auto* Move=State.Moves.Find(O.Id);
        const bool ScriptWalking=Move && Move->Walking && Move->Duration>0;
        const float WalkSpeed=ScriptWalking?200.f/Move->Duration:200.f*Data->Story->MovementContract->GetIntegerField(TEXT("frames_per_second"))/Data->Story->MovementContract->GetIntegerField(TEXT("walk_frames"));
        A->SetSourceSeated(Chair&&!O.AutonomousMoving&&!Move);A->SetSourceWalk(O.AutonomousMoving||ScriptWalking,WalkSpeed);A->SetSourceVisible(O.Visible);
        if(Data->bCaptureSweep && O.Visible)UE_LOG(LogTemp,Display,TEXT("EMERALD_CHARACTER_OBJECT map=%s id=%d gfx=%d symbol=%s tile=%d,%d"),*State.Map,O.Id,O.Graphics,*O.GraphicsName,O.Tile.X,O.Tile.Y);
        if(O.Visible){if(Profile.IsValid()){++Expected;if(A->IsReady())++Rendered;}else ++Diagnostics;}
    }
    if(PlayerFigure)
    {
        PlayerFigure->SetSourceVisible(!State.PlayerHidden&&!Data->bCaptureSweep);PlayerFigure->SetSourceFacing(State.PlayerFacing);
        Body->SetVisibility(!PlayerFigure->IsReady()&&!State.PlayerHidden&&!Data->bCaptureSweep);
    }
    else Body->SetVisibility(!State.PlayerHidden&&!Data->bCaptureSweep);
    if(Data->bCaptureSweep)UE_LOG(LogTemp,Display,TEXT("EMERALD_CHARACTER_SCENE map=%s expected=%d rendered=%d diagnostics=%d"),*MapId,Expected,Rendered,Diagnostics);
}

AEmeraldGameMode::AEmeraldGameMode()
{
    DefaultPawnClass=AEmeraldPawn::StaticClass();
    HUDClass=AEmeraldHUD::StaticClass();
}

void AEmeraldHUD::DrawHUD()
{
    Super::DrawHUD();if(!Canvas||!GetWorld()->GetGameInstance())return;
    const auto* CreditsPawn=Cast<AEmeraldPawn>(GetOwningPawn());
    if(CreditsPawn && CreditsPawn->CreditsVisible())
    {
        const float W=Canvas->SizeX,H=Canvas->SizeY;UFont* Font=GEngine->GetMediumFont();
        DrawRect(FLinearColor(.025f,.04f,.035f,.97f),W*.025f,H*.035f,W*.95f,H*.93f);
        DrawText(TEXT("Credits"),FLinearColor(.9f,.97f,.92f,1),W*.055f,H*.075f,Font,H/570.f);
        float Y=H*.16f;
        for(const auto& Line:CreditsPawn->AssetCredits()){DrawText(Line,FLinearColor(.82f,.9f,.85f,1),W*.055f,Y,Font,H/1000.f);Y+=H*.038f;}
        DrawText(TEXT("C or Esc to close"),FLinearColor(.82f,.9f,.85f,1),W*.055f,H*.9f,Font,H/880.f);
        return;
    }
    const auto* Data=GetWorld()->GetGameInstance()->GetSubsystem<UEmeraldData>();
    if(!Data||!Data->Story||!Data->Story->Enabled)return;
    const auto& Story=*Data->Story;const float W=Canvas->SizeX,H=Canvas->SizeY;
    UFont* Font=GEngine->GetMediumFont();const float Scale=FMath::Max(.6f,H/600.f);
    if(Story.VM.WaitingClock)
    {
        DrawRect(FLinearColor(.04f,.06f,.1f,1),0,0,W,H);
        const auto* Pawn=Cast<AEmeraldPawn>(GetOwningPawn());const int32 Hour=Pawn?Pawn->ClockHour():Story.State.Hour,Minute=Pawn?Pawn->ClockMinute():Story.State.Minute;
        const FVector2D Center(W*.5f,H*.43f);const float Radius=H*.25f;
        for(int32 I=0;I<60;++I)
        {
            const float A=I*2*PI/60;const FVector2D D(FMath::Sin(A),-FMath::Cos(A));
            DrawLine(Center.X+D.X*Radius*.9f,Center.Y+D.Y*Radius*.9f,Center.X+D.X*Radius,Center.Y+D.Y*Radius,FLinearColor::White,I%5==0?3:1);
        }
        const float MA=Minute*2*PI/60,HA=(Hour%12+Minute/60.f)*2*PI/12;
        DrawLine(Center.X,Center.Y,Center.X+FMath::Sin(MA)*Radius*.8f,Center.Y-FMath::Cos(MA)*Radius*.8f,FLinearColor::White,4);
        DrawLine(Center.X,Center.Y,Center.X+FMath::Sin(HA)*Radius*.55f,Center.Y-FMath::Cos(HA)*Radius*.55f,FLinearColor(.7f,.85f,1,1),6);
        DrawText(FString::Printf(TEXT("%02d:%02d"),Hour,Minute),FLinearColor::White,W*.43f,H*.76f,Font,Scale*1.8f);
        return;
    }
    if(Story.Dialogue.IsEmpty())return;
    const float X=W*.035f,Y=H*.74f,BW=W*.93f,BH=H*.225f;
    DrawRect(FLinearColor(.04f,.09f,.16f,1),X-6,Y-6,BW+12,BH+12);DrawRect(FLinearColor(.95f,.96f,.9f,1),X,Y,BW,BH);
    TArray<FString> Lines;Story.Dialogue.ParseIntoArrayLines(Lines,false);
    float PY=Y+H*.022f;
    for(const auto& Line:Lines){DrawText(Line,FLinearColor(.03f,.06f,.1f,1),X+W*.025f,PY,Font,H/240.f);PY+=H*.064f;}
    if(Story.YesNo)DrawText(TEXT("YES / NO"),FLinearColor(.03f,.06f,.1f,1),X+BW-W*.17f,Y+BH-H*.04f,Font,Scale*.85f);
}

void AEmeraldPawn::TickEventSmoke(float Seconds)
{
    if(!Data||!Data->Story)return;
    auto* PC=Cast<APlayerController>(GetController());if(!PC)return;
    auto& R=*Data->Story;Data->EventSeconds+=Seconds;Data->EventStageSeconds+=Seconds;
    auto Key=[&](FKey K,EInputEvent Event){return PC->InputKey(FInputKeyEventArgs(nullptr,IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(),K,Event,FPlatformTime::Cycles64()));};
    auto Press=[&](FKey K){Key(K,IE_Pressed);Data->EventReleaseKey=K;};
    auto Stage=[&](int32 Value){Data->EventStage=Value;Data->EventStageSeconds=0;};
    if(Data->EventReleaseKey.IsValid()){Key(Data->EventReleaseKey,IE_Released);Data->EventReleaseKey=FKey();}
    if(Data->EventSeconds>30){Data->FinishEventSmoke(false,TEXT("Timed out waiting for native key/script path"));return;}
    if(!R.LastError.IsEmpty()){Data->FinishEventSmoke(false,R.LastError);return;}
    const float Dwell=Data->EventShotDirectory.IsEmpty()?0.f:3.f;
    if(!bCameraSmokeDone)
    {
        if(CameraSmokeStage==0){CameraSmokeTile=Tile;Press(EKeys::V);CameraSmokeStage=1;return;}
        if(CameraSmokeStage==1)
        {
            if(!Data->bThirdPersonView||Camera->ProjectionMode!=ECameraProjectionMode::Perspective||Tile!=CameraSmokeTile){Data->FinishEventSmoke(false,TEXT("V did not enable third-person camera without moving source tile"));return;}
            Press(EKeys::V);CameraSmokeStage=2;return;
        }
        if(Data->bThirdPersonView||Camera->ProjectionMode!=ECameraProjectionMode::Orthographic||Tile!=CameraSmokeTile){Data->FinishEventSmoke(false,TEXT("V did not restore overhead camera without moving source tile"));return;}
        UE_LOG(LogTemp,Display,TEXT("EMERALD_CAMERA_INPUT_VERIFIED perspective=1 overhead=1 tile_unchanged=1"));bCameraSmokeDone=true;return;
    }
    if(!bCreditsSmokeDone)
    {
        if(CreditsSmokeStage==0)
        {
            Press(EKeys::C);
            CreditsSmokeStage=1;Data->EventStageSeconds=0;return;
        }
        if(CreditsSmokeStage==1)
        {
            if(!bCreditsVisible){if(Data->EventStageSeconds>1)Data->FinishEventSmoke(false,TEXT("C did not open credits"));return;}
            const FIntPoint Before=Tile;
            if(TryStep({0,1})||Tile!=Before){Data->FinishEventSmoke(false,TEXT("Credits movement isolation failed"));return;}
            CreditsSmokeStage=2;Data->EventStageSeconds=0;return;
        }
        if(CreditsSmokeStage==2)
        {
            if(Data->EventStageSeconds<Dwell)return;
            if(!Data->EventShotDirectory.IsEmpty())FScreenshotRequest::RequestScreenshot(Data->EventShotDirectory/TEXT("asset-credits.png"),false,false);
            CreditsSmokeStage=3;Data->EventStageSeconds=0;return;
        }
        if(CreditsSmokeStage==3)
        {
            if(Data->EventStageSeconds<(Data->EventShotDirectory.IsEmpty()?0.f:.5f))return;
            Press(EKeys::Escape);CreditsSmokeStage=4;Data->EventStageSeconds=0;return;
        }
        if(bCreditsVisible){if(Data->EventStageSeconds>1)Data->FinishEventSmoke(false,TEXT("Escape did not close credits"));return;}
        bCreditsSmokeDone=true;Data->EventStageSeconds=0;
        UE_LOG(LogTemp,Display,TEXT("EMERALD_CREDITS_INPUT open=1 movement_blocked=1 closed=1"));return;
    }
    if(Data->EventStage==0)
    {
        if(R.State.Objects[1].Tile!=FIntPoint(7,2)||!R.State.Objects[1].Visible||R.State.Objects[4].Visible)
        {Data->FinishEventSmoke(false,TEXT("Source NPC callback/visibility mismatch"));return;}
        Press(EKeys::E);Stage(1);
    }
    else if(Data->EventStage==1 && R.VM.WaitingDialogue)
    {
        if(!R.Dialogue.Contains(TEXT("LITTLEROOT"))){Data->FinishEventSmoke(false,TEXT("E dispatched wrong source sign"));return;}
        if(Data->EventStageSeconds<Dwell)return;
        if(!Data->EventShotDirectory.IsEmpty())FScreenshotRequest::RequestScreenshot(Data->EventShotDirectory/TEXT("source-town-sign.png"),false,false);
        Press(EKeys::E);Stage(2);
    }
    else if(Data->EventStage==2 && !R.IsLocked())
    {
        Tile={10,2};Facing={0,-1};R.State.PlayerTile=Tile;R.State.PlayerDraw=FVector2D(Tile);R.State.PlayerFacing=2;SetActorLocation(FVector(2000,400,0));
        Press(EKeys::W);Stage(3);
    }
    else if(Data->EventStage==3)
    {
        // The real held key is polled by Pawn::Tick and enters the source coord trigger.
        if(Tile==FIntPoint(10,1)){Key(EKeys::W,IE_Released);if(!bMoving&&R.VM.Busy)Stage(4);}
        else Key(EKeys::W,IE_Pressed);
    }
    else if(Data->EventStage==4)
    {
        if(R.VM.WaitingDialogue)
        {
            if(Data->EventStageSeconds<Dwell)return;
            if(!Data->EventShotDirectory.IsEmpty() && R.Dialogue.Contains(TEXT("grass")))FScreenshotRequest::RequestScreenshot(Data->EventShotDirectory/TEXT("source-route-guard.png"),false,false);
            Press(EKeys::E);Data->EventStageSeconds=0;
        }
        else if(!R.VM.Busy)
        {
            if(R.State.PlayerTile!=FIntPoint(10,2)||R.State.Objects[1].Tile!=FIntPoint(7,2))
            {Data->FinishEventSmoke(false,TEXT("Original guard sequence did not restore source positions"));return;}
            Stage(5);Data->FinishEventSmoke(true,TEXT("E sign and W original coordinate-guard sequence passed through native keyboard dispatch"));
        }
    }
}

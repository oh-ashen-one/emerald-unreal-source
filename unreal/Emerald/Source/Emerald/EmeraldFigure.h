#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EmeraldFigure.generated.h"
class USkeletalMeshComponent;
class UStaticMeshComponent;
class UAnimSequence;
class FJsonObject;

UCLASS()
class EMERALD_API AEmeraldFigure : public AActor
{
    GENERATED_BODY()
public:
    AEmeraldFigure();
    virtual void BeginPlay() override;
    bool Configure(const FString& Key,const TSharedPtr<FJsonObject>& Profile);
    void SetSourceVisible(bool Visible);
    void SetSourceFacing(int32 Facing);
    void SetSourceWalk(bool Walking,float SourceSpeed) {bSourceGait=true;bSourceWalk=Walking;SourceWalkSpeed=SourceSpeed;}
    void SetSourceSeated(bool Seated) {bSeated=Seated;}
    bool IsReady() const {return bReady;}
    virtual void Tick(float Seconds) override;
    // Serialized only on task-owned /Game/QualityGallery preview actors.
    UPROPERTY(EditAnywhere,Category="Emerald|Preview") FString PreviewProfile;
    UPROPERTY(EditAnywhere,Category="Emerald|Preview") FString PreviewRole;
    UPROPERTY(EditAnywhere,Category="Emerald|Preview") TObjectPtr<UAnimSequence> PreviewAnimation;
private:
    UPROPERTY() TObjectPtr<USkeletalMeshComponent> Visual;
    UPROPERTY() TArray<TObjectPtr<USkeletalMeshComponent>> AdditionalVisuals;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Diagnostic;
    UPROPERTY() TObjectPtr<UAnimSequence> Idle;
    UPROPERTY() TObjectPtr<UAnimSequence> Walk;
    UPROPERTY() TObjectPtr<UAnimSequence> Run;
    UPROPERTY() TObjectPtr<UAnimSequence> Current;
    UPROPERTY() TObjectPtr<UAnimSequence> Sit;
    FString ProfileKey;
    bool bReady=false,bVisible=false,bHasPosition=false,bPlaybackLogged=false,bHasProbe=false;
    FVector PreviousPosition,ProbeMin,ProbeMax;
    FVector VisualBaseLocation=FVector::ZeroVector,SeatedVisualOffset=FVector::ZeroVector;
    float PreviousTime=0,ForwardYaw=0,MotionScale=1,SourceWalkSpeed=0;
    bool bSeated=false,bStatic=false,bSourceWalk=false,bSourceGait=false,bPreviewActive=false;
    int32 ProbeIndex=INDEX_NONE,ProbeSamples=0;
};

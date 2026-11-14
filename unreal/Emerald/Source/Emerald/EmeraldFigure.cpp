#include "EmeraldFigure.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Materials/MaterialInterface.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Engine/World.h"

AEmeraldFigure::AEmeraldFigure()
{
    PrimaryActorTick.bCanEverTick=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("SourceFootAnchor"));
    Visual=CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("LicensedCharacter"));Visual->SetupAttachment(RootComponent);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Visual->bEnableUpdateRateOptimizations=false;
    Visual->PrimaryComponentTick.AddPrerequisite(this,PrimaryActorTick);
    Diagnostic=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ExplicitMissingCharacter"));Diagnostic->SetupAttachment(RootComponent);
    Diagnostic->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Diagnostic->SetRelativeLocation(FVector(0,0,65));Diagnostic->SetRelativeScale3D(FVector(.65,.65,1.3));
    Tags.Add(TEXT("EmeraldRuntimeFigure"));
}

void AEmeraldFigure::BeginPlay()
{
    Super::BeginPlay();
    if(PreviewProfile.IsEmpty())return;
    if(!GetWorld()->GetOutermost()->GetName().StartsWith(TEXT("/Game/QualityGallery/")))return;
    TSharedPtr<FJsonObject> Profile;
    if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(PreviewProfile),Profile) || !Configure(TEXT("Preview_")+PreviewRole,Profile))
    {UE_LOG(LogTemp,Error,TEXT("EMERALD_CHARACTER_LOAD_FAILED preview=%s"),*PreviewRole);return;}
    bPreviewActive=true;SetSourceVisible(true);
}

bool AEmeraldFigure::Configure(const FString& Key,const TSharedPtr<FJsonObject>& Profile)
{
    if(ProfileKey==Key)return bReady;
    ProfileKey=Key;bReady=false;bHasPosition=false;Current=nullptr;
    SeatedVisualOffset=FVector::ZeroVector;
    for(const auto& Part:AdditionalVisuals)if(Part)Part->DestroyComponent();
    AdditionalVisuals.Reset();
    if(Profile.IsValid() && Profile->HasField(TEXT("kind")) && Profile->GetStringField(TEXT("kind"))==TEXT("static"))
    {
        bStatic=true;Visual->SetVisibility(false);Visual->SetComponentTickEnabled(false);
        auto* Mesh=LoadObject<UStaticMesh>(nullptr,*Profile->GetStringField(TEXT("static_mesh")));
        const auto& Mats=Profile->GetArrayField(TEXT("materials"));
        auto* Mat=Mats.Num()?LoadObject<UMaterialInterface>(nullptr,*Mats[0]->AsString()):nullptr;
        bReady=Mesh && Mat;
        if(bReady)
        {
            const float Diameter=Profile->GetNumberField(TEXT("diameter_cm"));Diagnostic->SetStaticMesh(Mesh);
            for(int32 Index=0;Index<Mats.Num();++Index)Diagnostic->SetMaterial(Index,LoadObject<UMaterialInterface>(nullptr,*Mats[Index]->AsString()));
            const FBoxSphereBounds Bounds=Mesh->GetBounds();
            const float Scale=Diameter/FMath::Max(2*Bounds.BoxExtent.Z,UE_SMALL_NUMBER);
            Diagnostic->SetRelativeScale3D(FVector(Scale));
            Diagnostic->SetRelativeLocation(FVector(-Bounds.Origin.X,-Bounds.Origin.Y,Bounds.BoxExtent.Z-Bounds.Origin.Z)*Scale);
        }
        Diagnostic->SetVisibility(bReady);UE_LOG(LogTemp,Display,TEXT("EMERALD_CHARACTER_STATIC role=%s ready=%d"),*Key,bReady?1:0);return bReady;
    }
    bStatic=false;
    if(Profile.IsValid())
    {
        auto* Mesh=LoadObject<USkeletalMesh>(nullptr,*Profile->GetStringField(TEXT("mesh")));
        const auto& Anims=Profile->GetObjectField(TEXT("animations"));
        Idle=LoadObject<UAnimSequence>(nullptr,*Anims->GetStringField(TEXT("Idle")));
        Walk=LoadObject<UAnimSequence>(nullptr,*Anims->GetStringField(TEXT("Walk")));
        Run=LoadObject<UAnimSequence>(nullptr,*Anims->GetStringField(TEXT("Run")));
        Sit=LoadObject<UAnimSequence>(nullptr,*Anims->GetStringField(TEXT("SitDown")));
        if(Mesh && Idle && Walk && Run && Sit && Mesh->GetRefSkeleton().GetNum()>=Profile->GetIntegerField(TEXT("source_joint_count")))
        {
            const auto B=Mesh->GetBounds();FVector Origin=B.Origin,Extent=B.BoxExtent;
            if(Profile->HasField(TEXT("bounds_origin")) && Profile->HasField(TEXT("bounds_extent")))
            {
                const auto& O=Profile->GetArrayField(TEXT("bounds_origin"));const auto& E=Profile->GetArrayField(TEXT("bounds_extent"));
                if(O.Num()==3 && E.Num()==3){Origin=FVector(O[0]->AsNumber(),O[1]->AsNumber(),O[2]->AsNumber());Extent=FVector(E[0]->AsNumber(),E[1]->AsNumber(),E[2]->AsNumber());}
            }
            const float Scale=Profile->GetNumberField(TEXT("height_cm"))/FMath::Max(2.*Extent.Z,1.);
            MotionScale=Scale*(Profile->HasField(TEXT("animation_speed_scale"))?Profile->GetNumberField(TEXT("animation_speed_scale")):1.);
            Visual->EmptyOverrideMaterials();
            Visual->SetSkeletalMeshAsset(Mesh);
            Visual->SetRelativeScale3D(FVector(Scale*Profile->GetNumberField(TEXT("width_scale")),Scale,Scale));
            VisualBaseLocation=FVector(0,0,-(Origin.Z-Extent.Z)*Scale);
            if(Profile->HasField(TEXT("seated_offset_cm")))
            {
                const auto& Offset=Profile->GetArrayField(TEXT("seated_offset_cm"));
                if(Offset.Num()!=3)return false;
                SeatedVisualOffset=FVector(Offset[0]->AsNumber(),Offset[1]->AsNumber(),Offset[2]->AsNumber());
            }
            Visual->SetRelativeLocation(VisualBaseLocation);
            ForwardYaw=Profile->GetNumberField(TEXT("forward_yaw"));
            const auto& Materials=Profile->GetArrayField(TEXT("materials"));
            bool ValidMaterials=Materials.Num()==Visual->GetNumMaterials();
            for(int32 I=0;I<Materials.Num();++I)
            {
                auto* Mat=LoadObject<UMaterialInterface>(nullptr,*Materials[I]->AsString());
                ValidMaterials&=Mat!=nullptr;if(Mat)Visual->SetMaterial(I,Mat);
            }
            if(Profile->HasField(TEXT("mesh_parts")))for(const auto& Value:Profile->GetArrayField(TEXT("mesh_parts")))
            {
                const auto P=Value->AsObject();auto* PartMesh=LoadObject<USkeletalMesh>(nullptr,*P->GetStringField(TEXT("mesh")));
                if(!PartMesh || PartMesh->GetSkeleton()!=Mesh->GetSkeleton() || PartMesh->GetRefSkeleton().GetNum()!=Mesh->GetRefSkeleton().GetNum()){ValidMaterials=false;continue;}
                auto* Part=NewObject<USkeletalMeshComponent>(this,MakeUniqueObjectName(this,USkeletalMeshComponent::StaticClass(),FName(*FString::Printf(TEXT("LicensedPart_%d"),AdditionalVisuals.Num()))));
                AddInstanceComponent(Part);Part->SetupAttachment(RootComponent);Part->SetSkeletalMeshAsset(PartMesh);Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                Part->SetRelativeTransform(Visual->GetRelativeTransform());Part->SetLeaderPoseComponent(Visual,true,false);Part->bEnableUpdateRateOptimizations=false;
                const auto& PartMaterials=P->GetArrayField(TEXT("materials"));ValidMaterials&=PartMaterials.Num()==Part->GetNumMaterials();
                for(int32 I=0;I<PartMaterials.Num();++I){auto* Mat=LoadObject<UMaterialInterface>(nullptr,*PartMaterials[I]->AsString());ValidMaterials&=Mat!=nullptr;if(Mat)Part->SetMaterial(I,Mat);}
                Part->RegisterComponent();AdditionalVisuals.Add(Part);
            }
            ProbeIndex=INDEX_NONE;
            const FString ProbeName=Profile->HasField(TEXT("probe_bone"))?Profile->GetStringField(TEXT("probe_bone")):TEXT("Fist_L");
            for(int32 I=0;I<Mesh->GetRefSkeleton().GetNum();++I)
            {
                const FString Name=Mesh->GetRefSkeleton().GetBoneName(I).ToString().Replace(TEXT("."),TEXT("_"));
                if(Name==ProbeName)ProbeIndex=I;
            }
            bReady=ValidMaterials;
            UE_LOG(LogTemp,Display,TEXT("EMERALD_CHARACTER_CONFIG role=%s bones=%d materials=%d ready=%d probe=%d parts=%d"),*Key,Mesh->GetRefSkeleton().GetNum(),Materials.Num(),bReady?1:0,ProbeIndex,AdditionalVisuals.Num()+1);
        }
        if(!bReady)UE_LOG(LogTemp,Error,TEXT("EMERALD_CHARACTER_LOAD_FAILED role=%s"),*Key);
    }
    Visual->SetVisibility(bReady);
    Diagnostic->SetVisibility(!bReady);
    if(!bReady)
    {
        Diagnostic->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cylinder.Cylinder")));
        Diagnostic->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Imported/Materials/MI_Diagnostic.MI_Diagnostic")));
    }
    return bReady;
}

void AEmeraldFigure::SetSourceVisible(bool Visible)
{
    if(bVisible!=Visible)bHasPosition=false;
    bVisible=Visible;SetActorHiddenInGame(!Visible);SetActorTickEnabled(Visible);Visual->SetComponentTickEnabled(Visible&&!bStatic);
}

void AEmeraldFigure::SetSourceFacing(int32 Facing)
{
    const float Yaw=Facing==2?180.f:Facing==3?90.f:Facing==4?-90.f:0.f;
    SetActorRotation(FRotator(0,Yaw+ForwardYaw,0));
}

void AEmeraldFigure::Tick(float Seconds)
{
    Super::Tick(Seconds);
    const FVector Position=GetActorLocation();const FVector Delta=bHasPosition?Position-PreviousPosition:FVector::ZeroVector;
    PreviousPosition=Position;bHasPosition=true;
    if(!bReady||bStatic)return;
    const float Speed=bSourceGait?(bSourceWalk?SourceWalkSpeed:0.f):Seconds>SMALL_NUMBER?Delta.Size2D()/Seconds:0.f;
    UAnimSequence* Selected=bPreviewActive&&PreviewAnimation?PreviewAnimation.Get():bSeated && Speed<=1?Sit.Get():Speed>400&&!bSourceWalk?Run.Get():Speed>1?Walk.Get():Idle.Get();
    if(Selected!=Current)
    {
        const FVector Location=VisualBaseLocation+(Selected==Sit?SeatedVisualOffset:FVector::ZeroVector);
        Visual->SetRelativeLocation(Location);
        for(const auto& Part:AdditionalVisuals)if(Part)Part->SetRelativeLocation(Location);
        Current=Selected;Visual->PlayAnimation(Selected,Selected!=Sit);
        if(Selected==Sit){Visual->SetPosition(FMath::Max(0.f,Sit->GetPlayLength()-1.f/30.f),false);UE_LOG(LogTemp,Display,TEXT("EMERALD_CHARACTER_SEATED role=%s clip=%s visual_offset_cm=%.3f,%.3f,%.3f"),*ProfileKey,*Sit->GetName(),SeatedVisualOffset.X,SeatedVisualOffset.Y,SeatedVisualOffset.Z);}
        bHasProbe=false;bPlaybackLogged=false;ProbeSamples=0;PreviousTime=0;
    }
    float Rate=Selected==Sit?0.f:Speed>400&&!bSourceWalk?FMath::Clamp(Speed/((Run==Walk?200.f:600.f)*MotionScale),.5f,6.f):Speed>1?FMath::Clamp(Speed/(200.f*MotionScale),.5f,6.f):1.f;
    if(bPreviewActive && PreviewAnimation && Selected!=Sit)Rate=1.f;
    if(Speed>1 && FVector::DotProduct(Delta,GetActorRotation().RotateVector(FVector(0,1,0)))<0)Rate=-Rate;
    Visual->SetPlayRate(Rate);
    const auto* Instance=Visual->GetSingleNodeInstance();const auto& Pose=Visual->GetComponentSpaceTransforms();
    if(Instance && Pose.IsValidIndex(ProbeIndex))
    {
        const float Time=Instance->GetCurrentTime();const FVector P=Pose[ProbeIndex].GetLocation();
        if(ProbeSamples<6){++ProbeSamples;PreviousTime=Time;return;}
        if(!bHasProbe){ProbeMin=ProbeMax=P;bHasProbe=true;}
        else {ProbeMin=ProbeMin.ComponentMin(P);ProbeMax=ProbeMax.ComponentMax(P);}
        ++ProbeSamples;
        if(!bPlaybackLogged && ProbeSamples>=(Current==Walk?10:18) && FMath::Abs(Time-PreviousTime)>1e-5 && (ProbeMax-ProbeMin).Size()>.01)
        {
            UE_LOG(LogTemp,Display,TEXT("EMERALD_CHARACTER_PLAYBACK role=%s clip=%s time=%.3f component_bone_range_cm=%.4f samples=%d rate=%.3f"),*ProfileKey,*Current->GetName(),Time,(ProbeMax-ProbeMin).Size(),ProbeSamples,Rate);
            bPlaybackLogged=true;
        }
        PreviousTime=Time;
    }
}

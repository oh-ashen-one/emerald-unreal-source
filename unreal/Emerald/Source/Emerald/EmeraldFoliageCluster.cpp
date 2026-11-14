#include "EmeraldFoliageCluster.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
AEmeraldFoliageCluster::AEmeraldFoliageCluster()
{
    PrimaryActorTick.bCanEverTick=false;
    Foliage=CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("SourceFoliageInstances"));
    RootComponent=Foliage;
    Foliage->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Foliage->SetMobility(EComponentMobility::Static);
    Foliage->bAutoRebuildTreeOnInstanceChanges=false;
    Tags.Add(TEXT("EmeraldGenerated"));
}
void AEmeraldFoliageCluster::FinalizeInstances()
{
    Foliage->BuildTreeIfOutdated(false,true);
    Foliage->MarkRenderStateDirty();
}

void AEmeraldFoliageCluster::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp,Display,TEXT("EMERALD_FOLIAGE_RUNTIME actor=%s instances=%d collision=%d"),*GetName(),Foliage->GetInstanceCount(),static_cast<int32>(Foliage->GetCollisionEnabled()));
}

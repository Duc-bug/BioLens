"""
Định nghĩa Schema dữ liệu cho REST API của BioLens (Pydantic Schemas).
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class TaxonomySchema(BaseModel):
    kingdom: str = ""
    kingdomVn: str = ""
    phylum: str = ""
    classVn: str = ""
    order: str = ""
    family: str = ""
    familyVn: str = ""
    genus: str = ""


class ProfileSectionsSchema(BaseModel):
    overview: str
    morphologyFlower: str
    morphologyLeafStem: str
    habitatDistribution: str
    partsUsed: str
    medicinalUses: str
    safetyWarning: str
    hasWikiExtract: bool = False


class SpeciesDetailSchema(BaseModel):
    speciesKey: str
    primaryVietnameseName: str
    vietnameseAliases: List[str] = []
    canonicalName: str
    scientificName: str
    vernacularNameEn: str = ""
    taxonomy: Dict[str, Any]
    profileSections: ProfileSectionsSchema
    externalLinks: Dict[str, str]
    totalDatasetImages: int = 0
    sampleImageUrls: List[str] = []


class IdentifyResponseSchema(BaseModel):
    isAccepted: bool
    selectedAlgorithm: str
    organHint: str
    inferenceTimeMs: float
    oodCheck: Dict[str, Any]
    message: Optional[str] = None
    topMatch: Optional[Dict[str, Any]] = None
    candidates: List[Dict[str, Any]] = []
    algorithmComparison: Dict[str, Any] = {}
    nutraceutical: Optional[Dict[str, Any]] = None


class NutraceuticalRecommendRequest(BaseModel):
    speciesKey: str
    healthGoal: Optional[str] = None
    userConstitution: Optional[str] = None


class NutraceuticalSymptomSearchRequest(BaseModel):
    query: str
    userConstitution: Optional[str] = None
    gradeFilter: Optional[str] = None
    topK: int = 8


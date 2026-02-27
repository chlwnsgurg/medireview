from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Hospital, AutomationRule
from schemas import HospitalCreate, HospitalOut, HospitalUpdate

router = APIRouter(prefix="/api/hospital", tags=["hospital"])


@router.get("", response_model=HospitalOut)
def get_hospital(db: Session = Depends(get_db)):
    """병원 정보 조회 (MVP: 단일 병원)"""
    hospital = db.query(Hospital).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="병원 정보가 없습니다. 먼저 등록해주세요.")
    return hospital


@router.post("", response_model=HospitalOut, status_code=201)
def create_hospital(data: HospitalCreate, db: Session = Depends(get_db)):
    """병원 정보 최초 등록"""
    existing = db.query(Hospital).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 병원 정보가 등록되어 있습니다.")

    hospital = Hospital(**data.model_dump())
    db.add(hospital)
    db.commit()
    db.refresh(hospital)

    # 자동화 규칙도 기본값으로 함께 생성
    rule = AutomationRule(hospital_id=hospital.id)
    db.add(rule)
    db.commit()

    return hospital


@router.put("", response_model=HospitalOut)
def update_hospital(data: HospitalUpdate, db: Session = Depends(get_db)):
    """병원 정보 수정"""
    hospital = db.query(Hospital).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="병원 정보가 없습니다.")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(hospital, key, value)

    db.commit()
    db.refresh(hospital)
    return hospital

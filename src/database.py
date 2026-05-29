"""SQLite Database Module for InstSpec"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import asdict
import uuid

from sqlalchemy import create_engine, Column, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config import config

Base = declarative_base()


class Project(Base):
    """Project table"""
    __tablename__ = 'projects'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    client = Column(String)
    location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Instrument(Base):
    """Instrument table"""
    __tablename__ = 'instruments'

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    tag_number = Column(String, nullable=False)
    instrument_type = Column(String, nullable=False)
    service = Column(String)
    line_number = Column(String)
    fluid_type = Column(String)
    fluid_name = Column(String)
    sizing_data = Column(Text, nullable=False)
    datasheet_data = Column(Text)
    status = Column(String, default='draft')
    revision = Column(String, default='A')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Revision(Base):
    """Revision table"""
    __tablename__ = 'revisions'

    id = Column(String, primary_key=True)
    instrument_id = Column(String, nullable=False)
    revision_letter = Column(String, nullable=False)
    date = Column(String, nullable=False)
    description = Column(Text)
    prepared_by = Column(String)
    checked_by = Column(String)
    approved_by = Column(String)
    changes = Column(Text)
    sizing_data = Column(Text, nullable=False)
    datasheet_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class FluidPreset(Base):
    """Fluid preset table"""
    __tablename__ = 'fluid_presets'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    coolprop_name = Column(String)
    default_properties = Column(Text)


class PipeSpec(Base):
    """Pipe specification table"""
    __tablename__ = 'pipe_specs'

    id = Column(String, primary_key=True)
    nominal_size = Column(String, nullable=False)
    schedule = Column(String, nullable=False)
    outside_diameter_mm = Column(Float, nullable=False)
    wall_thickness_mm = Column(Float, nullable=False)
    inside_diameter_mm = Column(Float, nullable=False)
    weight_per_m_kg = Column(Float, nullable=False)
    material_standard = Column(String, nullable=False)


class Database:
    """Database manager for InstSpec"""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection

        Args:
            db_path: Path to database file. If None, uses config.DATABASE_URL
        """
        if db_path:
            self.db_path = db_path
            self.engine = create_engine(f'sqlite:///{db_path}')
        else:
            self.engine = create_engine(config.DATABASE_URL.replace('sqlite:///', 'sqlite:///'))

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()

    # Project operations
    def create_project(self, name: str, description: str = None,
                      client: str = None, location: str = None) -> str:
        """Create a new project

        Args:
            name: Project name
            description: Project description
            client: Client name
            location: Location

        Returns:
            Project ID
        """
        session = self.get_session()
        try:
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                name=name,
                description=description,
                client=client,
                location=location
            )
            session.add(project)
            session.commit()
            return project_id
        finally:
            session.close()

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        session = self.get_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                return {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'client': project.client,
                    'location': project.location,
                    'created_at': project.created_at.isoformat(),
                    'updated_at': project.updated_at.isoformat()
                }
            return None
        finally:
            session.close()

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        session = self.get_session()
        try:
            projects = session.query(Project).all()
            return [{
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'client': p.client,
                'location': p.location,
                'created_at': p.created_at.isoformat()
            } for p in projects]
        finally:
            session.close()

    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project"""
        session = self.get_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                for key, value in kwargs.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                project.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()

    def delete_project(self, project_id: str) -> bool:
        """Delete project and all instruments"""
        session = self.get_session()
        try:
            # Delete all instruments in project first
            instruments = session.query(Instrument).filter(Instrument.project_id == project_id).all()
            for inst in instruments:
                session.delete(inst)

            # Delete project
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # Instrument operations
    def create_instrument(self, project_id: str, tag_number: str,
                         instrument_type: str, **kwargs) -> str:
        """Create a new instrument

        Args:
            project_id: Project ID
            tag_number: Instrument tag number
            instrument_type: Type of instrument
            **kwargs: Additional instrument fields

        Returns:
            Instrument ID
        """
        session = self.get_session()
        try:
            instrument_id = str(uuid.uuid4())
            instrument = Instrument(
                id=instrument_id,
                project_id=project_id,
                tag_number=tag_number,
                instrument_type=instrument_type,
                **kwargs
            )
            session.add(instrument)
            session.commit()
            return instrument_id
        finally:
            session.close()

    def get_instrument(self, instrument_id: str) -> Optional[Dict[str, Any]]:
        """Get instrument by ID"""
        session = self.get_session()
        try:
            instrument = session.query(Instrument).filter(Instrument.id == instrument_id).first()
            if instrument:
                return {
                    'id': instrument.id,
                    'project_id': instrument.project_id,
                    'tag_number': instrument.tag_number,
                    'instrument_type': instrument.instrument_type,
                    'service': instrument.service,
                    'line_number': instrument.line_number,
                    'fluid_type': instrument.fluid_type,
                    'fluid_name': instrument.fluid_name,
                    'sizing_data': json.loads(instrument.sizing_data) if instrument.sizing_data else None,
                    'datasheet_data': json.loads(instrument.datasheet_data) if instrument.datasheet_data else None,
                    'status': instrument.status,
                    'revision': instrument.revision,
                    'created_at': instrument.created_at.isoformat(),
                    'updated_at': instrument.updated_at.isoformat()
                }
            return None
        finally:
            session.close()

    def list_instruments(self, project_id: str) -> List[Dict[str, Any]]:
        """List all instruments in a project"""
        session = self.get_session()
        try:
            instruments = session.query(Instrument).filter(Instrument.project_id == project_id).all()
            return [{
                'id': inst.id,
                'tag_number': inst.tag_number,
                'instrument_type': inst.instrument_type,
                'service': inst.service,
                'line_number': inst.line_number,
                'status': inst.status,
                'revision': inst.revision,
                'updated_at': inst.updated_at.isoformat()
            } for inst in instruments]
        finally:
            session.close()

    def update_instrument(self, instrument_id: str, **kwargs) -> bool:
        """Update instrument"""
        session = self.get_session()
        try:
            instrument = session.query(Instrument).filter(Instrument.id == instrument_id).first()
            if instrument:
                for key, value in kwargs.items():
                    if hasattr(instrument, key):
                        # If it's a dict, serialize to JSON
                        if isinstance(value, (dict, list)):
                            setattr(instrument, key, json.dumps(value))
                        else:
                            setattr(instrument, key, value)
                instrument.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()

    def delete_instrument(self, instrument_id: str) -> bool:
        """Delete instrument"""
        session = self.get_session()
        try:
            instrument = session.query(Instrument).filter(Instrument.id == instrument_id).first()
            if instrument:
                session.delete(instrument)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # Pipe spec operations
    def add_pipe_spec(self, nominal_size: str, schedule: str,
                     outside_diameter_mm: float, wall_thickness_mm: float,
                     inside_diameter_mm: float, weight_per_m_kg: float,
                     material_standard: str) -> str:
        """Add pipe specification"""
        session = self.get_session()
        try:
            spec_id = str(uuid.uuid4())
            pipe_spec = PipeSpec(
                id=spec_id,
                nominal_size=nominal_size,
                schedule=schedule,
                outside_diameter_mm=outside_diameter_mm,
                wall_thickness_mm=wall_thickness_mm,
                inside_diameter_mm=inside_diameter_mm,
                weight_per_m_kg=weight_per_m_kg,
                material_standard=material_standard
            )
            session.add(pipe_spec)
            session.commit()
            return spec_id
        finally:
            session.close()

    def get_pipe_spec(self, nominal_size: str, schedule: str) -> Optional[Dict[str, Any]]:
        """Get pipe specification by size and schedule"""
        session = self.get_session()
        try:
            pipe_spec = session.query(PipeSpec).filter(
                PipeSpec.nominal_size == nominal_size,
                PipeSpec.schedule == schedule
            ).first()
            if pipe_spec:
                return {
                    'id': pipe_spec.id,
                    'nominal_size': pipe_spec.nominal_size,
                    'schedule': pipe_spec.schedule,
                    'outside_diameter_mm': pipe_spec.outside_diameter_mm,
                    'wall_thickness_mm': pipe_spec.wall_thickness_mm,
                    'inside_diameter_mm': pipe_spec.inside_diameter_mm,
                    'weight_per_m_kg': pipe_spec.weight_per_m_kg,
                    'material_standard': pipe_spec.material_standard
                }
            return None
        finally:
            session.close()

    def list_pipe_sizes(self) -> List[str]:
        """List all available pipe nominal sizes"""
        session = self.get_session()
        try:
            sizes = session.query(PipeSpec.nominal_size).distinct().all()
            return [size[0] for size in sizes]
        finally:
            session.close()

    def list_pipe_schedules(self, nominal_size: str) -> List[str]:
        """List available schedules for a given pipe size"""
        session = self.get_session()
        try:
            schedules = session.query(PipeSpec.schedule).filter(
                PipeSpec.nominal_size == nominal_size
            ).distinct().all()
            return [schedule[0] for schedule in schedules]
        finally:
            session.close()

    # Fluid preset operations
    def add_fluid_preset(self, name: str, type: str, coolprop_name: str = None,
                        default_properties: Dict[str, Any] = None) -> str:
        """Add fluid preset"""
        session = self.get_session()
        try:
            preset_id = str(uuid.uuid4())
            fluid_preset = FluidPreset(
                id=preset_id,
                name=name,
                type=type,
                coolprop_name=coolprop_name,
                default_properties=json.dumps(default_properties) if default_properties else None
            )
            session.add(fluid_preset)
            session.commit()
            return preset_id
        finally:
            session.close()

    def list_fluid_presets(self) -> List[Dict[str, Any]]:
        """List all fluid presets"""
        session = self.get_session()
        try:
            presets = session.query(FluidPreset).all()
            return [{
                'id': preset.id,
                'name': preset.name,
                'type': preset.type,
                'coolprop_name': preset.coolprop_name,
                'default_properties': json.loads(preset.default_properties) if preset.default_properties else None
            } for preset in presets]
        finally:
            session.close()

    def get_fluid_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get fluid preset by ID"""
        session = self.get_session()
        try:
            preset = session.query(FluidPreset).filter(FluidPreset.id == preset_id).first()
            if preset:
                return {
                    'id': preset.id,
                    'name': preset.name,
                    'type': preset.type,
                    'coolprop_name': preset.coolprop_name,
                    'default_properties': json.loads(preset.default_properties) if preset.default_properties else None
                }
            return None
        finally:
            session.close()


# Global database instance
db = Database()
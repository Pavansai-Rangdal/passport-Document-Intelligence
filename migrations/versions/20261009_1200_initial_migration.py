"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-10-09 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('internal_id', sa.String(length=64), nullable=False),
        sa.Column('batch_id', sa.String(length=36), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('uploaded', 'processing', 'extracted', 'validated', 'failed', 'completed', name='documentstatus'), nullable=False),
        sa.Column('document_type', sa.Enum('passport_td1', 'passport_td2', 'passport_td3', 'id_card', 'unknown', name='documenttype'), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('dpi', sa.Integer(), nullable=True),
        sa.Column('blur_score', sa.Float(), nullable=True),
        sa.Column('brightness', sa.Float(), nullable=True),
        sa.Column('quality_passed', sa.Boolean(), nullable=True),
        sa.Column('mrz_detected', sa.Boolean(), nullable=False),
        sa.Column('mrz_type', sa.String(length=10), nullable=True),
        sa.Column('mrz_lines', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('internal_id')
    )
    op.create_index('ix_documents_batch_id', 'documents', ['batch_id'], unique=False)
    op.create_index('ix_documents_file_hash', 'documents', ['file_hash'], unique=False)
    op.create_index('ix_documents_status', 'documents', ['status'], unique=False)

    # Create batches table
    op.create_table(
        'batches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('internal_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.Enum('created', 'processing', 'completed', 'partial', 'failed', name='batchstatus'), nullable=False),
        sa.Column('total_documents', sa.Integer(), nullable=False),
        sa.Column('processed_documents', sa.Integer(), nullable=False),
        sa.Column('failed_documents', sa.Integer(), nullable=False),
        sa.Column('submitted_by', sa.String(length=255), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('internal_id')
    )
    op.create_index('ix_batches_status', 'batches', ['status'], unique=False)

    # Create passport_fields table
    op.create_table(
        'passport_fields',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('field_type', sa.Enum('surname', 'given_names', 'document_number', 'nationality', 'birth_date', 'sex', 'expiry_date', 'issuing_state', 'personal_number', 'place_of_birth', 'issue_date', name='fieldtype'), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_normalized', sa.Text(), nullable=True),
        sa.Column('source', sa.Enum('mrz', 'ocr_viz', 'ocr_mrz', 'manual', name='fieldsource'), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('ocr_engine', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_passport_fields_document_id', 'passport_fields', ['document_id'], unique=False)
    op.create_index('ix_passport_fields_field_type', 'passport_fields', ['field_type'], unique=False)

    # Create validation_results table
    op.create_table(
        'validation_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('rule_name', sa.String(length=255), nullable=False),
        sa.Column('rule_category', sa.Enum('schema', 'expiry', 'image_quality', 'cross_field', 'mrz_checksum', 'consistency', name='rulecategory'), nullable=False),
        sa.Column('severity', sa.Enum('error', 'warning', 'info', name='validationseverity'), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_validation_results_document_id', 'validation_results', ['document_id'], unique=False)
    op.create_index('ix_validation_results_passed', 'validation_results', ['passed'], unique=False)
    op.create_index('ix_validation_results_rule_name', 'validation_results', ['rule_name'], unique=False)

    # Create evidence table
    op.create_table(
        'evidence',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('evidence_type', sa.Enum('image_quality', 'mrz_detected', 'ocr_extraction', 'field_consistency', 'verification_attempt', 'system_one_decision', 'policy_evaluation', name='evidencetype'), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evidence_document_id', 'evidence', ['document_id'], unique=False)
    op.create_index('ix_evidence_evidence_type', 'evidence', ['evidence_type'], unique=False)

    # Create verification_attempts table
    op.create_table(
        'verification_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.Enum('system_one', 'issuer_database', 'lost_stolen_database', 'chip_authentication', name='verificationprovider'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'success', 'failed', 'timeout', 'unavailable', name='verificationstatus'), nullable=False),
        sa.Column('request_payload', postgresql.JSON(), nullable=True),
        sa.Column('response_payload', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_verification_attempts_document_id', 'verification_attempts', ['document_id'], unique=False)

    # Create decision_records table
    op.create_table(
        'decision_records',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('batch_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('outcome', sa.Enum('pass_screening', 'fail_rule', 'review_required', 'insufficient_data', name='decisionoutcome'), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('system_one_recommendation', sa.String(length=50), nullable=True),
        sa.Column('system_one_confidence', sa.Float(), nullable=True),
        sa.Column('policy_version', sa.String(length=50), nullable=True),
        sa.Column('policy_rules_triggered', postgresql.JSON(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('decision_metadata', postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decision_records_batch_id', 'decision_records', ['batch_id'], unique=False)
    op.create_index('ix_decision_records_document_id', 'decision_records', ['document_id'], unique=False)
    op.create_index('ix_decision_records_outcome', 'decision_records', ['outcome'], unique=False)

    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.Enum('document_uploaded', 'document_processed', 'extraction_completed', 'validation_completed', 'verification_attempted', 'decision_made', 'batch_created', 'batch_completed', 'error_occurred', 'security_alert', name='eventtype'), nullable=False),
        sa.Column('actor', sa.String(length=255), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_events_event_type', 'audit_events', ['event_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_events_event_type', table_name='audit_events')
    op.drop_table('audit_events')
    op.drop_index('ix_decision_records_outcome', table_name='decision_records')
    op.drop_index('ix_decision_records_document_id', table_name='decision_records')
    op.drop_index('ix_decision_records_batch_id', table_name='decision_records')
    op.drop_table('decision_records')
    op.drop_index('ix_verification_attempts_document_id', table_name='verification_attempts')
    op.drop_table('verification_attempts')
    op.drop_index('ix_evidence_evidence_type', table_name='evidence')
    op.drop_index('ix_evidence_document_id', table_name='evidence')
    op.drop_table('evidence')
    op.drop_index('ix_validation_results_rule_name', table_name='validation_results')
    op.drop_index('ix_validation_results_passed', table_name='validation_results')
    op.drop_index('ix_validation_results_document_id', table_name='validation_results')
    op.drop_table('validation_results')
    op.drop_index('ix_passport_fields_field_type', table_name='passport_fields')
    op.drop_index('ix_passport_fields_document_id', table_name='passport_fields')
    op.drop_table('passport_fields')
    op.drop_index('ix_batches_status', table_name='batches')
    op.drop_table('batches')
    op.drop_index('ix_documents_status', table_name='documents')
    op.drop_index('ix_documents_file_hash', table_name='documents')
    op.drop_index('ix_documents_batch_id', table_name='documents')
    op.drop_table('documents')

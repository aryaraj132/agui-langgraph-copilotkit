"""Tests for template, campaign, and custom_property schemas."""

import json


from agui_backend_demo.schemas.campaign import Campaign
from agui_backend_demo.schemas.custom_property import CustomProperty
from agui_backend_demo.schemas.template import EmailTemplate, TemplateSection


# ---------------------------------------------------------------------------
# TemplateSection
# ---------------------------------------------------------------------------


class TestTemplateSection:
    def test_creation(self):
        section = TemplateSection(id="s1", type="header", content="Hello")
        assert section.id == "s1"
        assert section.type == "header"
        assert section.content == "Hello"
        assert section.styles == {}

    def test_with_styles(self):
        section = TemplateSection(
            id="s2",
            type="body",
            content="World",
            styles={"color": "red", "font-size": "14px"},
        )
        assert section.styles == {"color": "red", "font-size": "14px"}

    def test_serialization_roundtrip(self):
        section = TemplateSection(
            id="s1", type="footer", content="Bye", styles={"margin": "10px"}
        )
        data = json.loads(section.model_dump_json())
        restored = TemplateSection(**data)
        assert restored == section


# ---------------------------------------------------------------------------
# EmailTemplate
# ---------------------------------------------------------------------------


class TestEmailTemplate:
    def test_defaults(self):
        template = EmailTemplate()
        assert template.html == ""
        assert template.css == ""
        assert template.subject == ""
        assert template.preview_text == ""
        assert template.sections == []
        assert template.version == 1

    def test_full_construction(self):
        sections = [
            TemplateSection(id="h1", type="header", content="<h1>Hi</h1>"),
            TemplateSection(id="b1", type="body", content="<p>Body</p>"),
        ]
        template = EmailTemplate(
            html="<html></html>",
            css="body { color: red; }",
            subject="Test Subject",
            preview_text="Preview",
            sections=sections,
            version=2,
        )
        assert template.subject == "Test Subject"
        assert len(template.sections) == 2
        assert template.version == 2

    def test_serialization_roundtrip(self):
        sections = [
            TemplateSection(
                id="s1", type="cta", content="Click", styles={"bg": "blue"}
            ),
        ]
        template = EmailTemplate(
            html="<html/>",
            css="h1{}",
            subject="Sub",
            preview_text="Pre",
            sections=sections,
            version=3,
        )
        data = json.loads(template.model_dump_json())
        restored = EmailTemplate(**data)
        assert restored == template


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------


class TestCampaign:
    def test_creation_minimal(self):
        campaign = Campaign(name="My Campaign")
        assert campaign.name == "My Campaign"
        assert campaign.segment_id is None
        assert campaign.template_id is None
        assert campaign.subject == ""
        assert campaign.send_time is None
        assert campaign.status == "draft"

    def test_full_construction(self):
        campaign = Campaign(
            name="Launch",
            segment_id="seg-1",
            template_id="tmpl-1",
            subject="Big Launch",
            send_time="2026-04-01T10:00:00Z",
            status="scheduled",
        )
        assert campaign.segment_id == "seg-1"
        assert campaign.status == "scheduled"

    def test_defaults(self):
        campaign = Campaign(name="X")
        assert campaign.status == "draft"
        assert campaign.subject == ""

    def test_serialization_roundtrip(self):
        campaign = Campaign(
            name="Test",
            segment_id="s1",
            template_id="t1",
            subject="Subj",
            send_time="2026-05-01T12:00:00Z",
            status="sent",
        )
        data = json.loads(campaign.model_dump_json())
        restored = Campaign(**data)
        assert restored == campaign


# ---------------------------------------------------------------------------
# CustomProperty
# ---------------------------------------------------------------------------


class TestCustomProperty:
    def test_creation_minimal(self):
        prop = CustomProperty(
            name="days_since_signup",
            description="Days since user signed up",
            javascript_code="return daysSince(user.created_at);",
        )
        assert prop.name == "days_since_signup"
        assert prop.property_type == "string"
        assert prop.example_value is None

    def test_full_construction(self):
        prop = CustomProperty(
            name="is_active",
            description="Whether user is active",
            javascript_code="return user.last_login > threshold;",
            property_type="boolean",
            example_value="true",
        )
        assert prop.property_type == "boolean"
        assert prop.example_value == "true"

    def test_defaults(self):
        prop = CustomProperty(name="x", description="d", javascript_code="return 1;")
        assert prop.property_type == "string"
        assert prop.example_value is None

    def test_serialization_roundtrip(self):
        prop = CustomProperty(
            name="score",
            description="Engagement score",
            javascript_code="return calc(user);",
            property_type="number",
            example_value="42",
        )
        data = json.loads(prop.model_dump_json())
        restored = CustomProperty(**data)
        assert restored == prop

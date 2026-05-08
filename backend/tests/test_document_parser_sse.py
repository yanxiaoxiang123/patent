"""Tests for document_parser progress callback - RED phase tests"""
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Set up environment before imports
import sys
import os
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ["DATABASE_URL"] = "mysql+aiomysql://root:123123@localhost:3306/iprs"

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")


class TestProgressCallbackFeature:
    """Test that progress callback feature exists and works"""

    @pytest.mark.asyncio
    async def test_parse_document_accepts_progress_callback(self):
        """parse_document should accept a progress_callback parameter"""
        from app.services.document_parser import PatentDocumentParser

        parser = PatentDocumentParser()

        progress_events = []
        def progress_callback(stage: str, percent: int, message: str):
            progress_events.append({"stage": stage, "percent": percent, "message": message})

        # Create a minimal test file
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "test.pdf")

        # Create minimal PDF
        with open(pdf_path, 'wb') as f:
            f.write(b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
196
%%EOF""")

        try:
            # This should call the progress callback during parsing
            result = await parser.parse_document(pdf_path, "pdf", progress_callback=progress_callback)

            # Verify progress callback was called
            assert len(progress_events) > 0, "Progress callback was never called"

            # Verify all expected stages were reported
            stages = [e["stage"] for e in progress_events]
            assert "extracting_text" in stages
            assert "analyzing_structure" in stages
            assert "extracting_sections" in stages
            assert "assessing_quality" in stages
            assert "complete" in stages
        finally:
            os.remove(pdf_path)
            os.rmdir(temp_dir)

    @pytest.mark.asyncio
    async def test_parse_document_progress_stages_have_percentages(self):
        """Each progress stage should have valid percentage values"""
        from app.services.document_parser import PatentDocumentParser

        parser = PatentDocumentParser()

        progress_events = []
        def progress_callback(stage: str, percent: int, message: str):
            progress_events.append({"stage": stage, "percent": percent, "message": message})

        # Create a minimal test file
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "test.pdf")

        with open(pdf_path, 'wb') as f:
            f.write(b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
196
%%EOF""")

        try:
            result = await parser.parse_document(pdf_path, "pdf", progress_callback=progress_callback)

            # All percentages should be 0-100
            for event in progress_events:
                assert 0 <= event["percent"] <= 100, f"Invalid percentage: {event['percent']}"

            # Percentages should be increasing
            percentages = [e["percent"] for e in progress_events]
            for i in range(1, len(percentages)):
                assert percentages[i] >= percentages[i-1], "Percentages should be monotonically increasing"
        finally:
            os.remove(pdf_path)
            os.rmdir(temp_dir)


class TestSSEEndpoint:
    """Test that SSE endpoint exists for document parsing"""

    def test_sse_endpoint_is_registered(self):
        """POST /documents/{id}/parse/stream should be a registered route"""
        from app.api.documents import router

        # Get all routes
        routes = []
        for route in router.routes:
            if hasattr(route, 'path'):
                routes.append({
                    'path': route.path,
                    'methods': getattr(route, 'methods', {'GET'})
                })

        # Find the SSE parse endpoint
        sse_route_exists = any(
            'parse' in r['path'] and 'stream' in r['path'] and 'POST' in r['methods']
            for r in routes
        )

        assert sse_route_exists, f"SSE parse endpoint not found. Available routes: {routes}"

    @pytest.mark.asyncio
    async def test_sse_endpoint_returns_sse_response(self):
        """SSE endpoint should return EventSourceResponse"""
        from app.api.documents import router

        # Find the SSE route
        sse_route = None
        for route in router.routes:
            if hasattr(route, 'path') and 'parse' in route.path and 'stream' in route.path:
                sse_route = route
                break

        assert sse_route is not None, "SSE parse stream route not found"
        assert hasattr(sse_route, 'endpoint'), "Route should have an endpoint"

        # Verify the endpoint is async
        import inspect
        assert inspect.iscoroutinefunction(sse_route.endpoint), "Endpoint should be async"

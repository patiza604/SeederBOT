from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.blackhole import BlackholeClient
from src.app.jackett import JackettClient


class TestJackettClient:

    @pytest.fixture
    def jackett_client(self):
        with patch('src.app.jackett.settings') as mock_settings:
            mock_settings.jackett_url = "http://test-jackett:9117"
            mock_settings.jackett_api_key = "test-key"
            mock_settings.categories = "2000,2010"
            mock_settings.min_seeders = 20
            mock_settings.quality_regex = r"1080p.*WEB-DL|1080p.*BluRay"
            mock_settings.exclude_regex = r"CAM|TS|TC|WORKPRINT"
            mock_settings.min_size_gb = 2.5
            mock_settings.max_size_gb = 6.0
            return JackettClient()

    @pytest.mark.asyncio
    async def test_search_torrents(self, jackett_client):
        """Test basic torrent search functionality"""

        # Mock XML response from Jackett
        mock_xml = '''<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0" xmlns:torznab="http://torznab.com/schemas/2015/feed">
            <channel>
                <item>
                    <title>Movie.2023.1080p.WEB-DL.x264</title>
                    <link>http://test.com/download/123</link>
                    <guid>123</guid>
                    <torznab:attr name="seeders" value="50"/>
                    <torznab:attr name="size" value="4294967296"/>
                </item>
            </channel>
        </rss>'''

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.text = mock_xml
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            results = await jackett_client.search_torrents("Test Movie 2023")

            assert len(results) == 1
            assert results[0]["title"] == "Movie.2023.1080p.WEB-DL.x264"
            assert results[0]["seeders"] == 50
            assert results[0]["size"] == 4294967296

    def test_filter_torrents(self, jackett_client):
        """Test torrent filtering logic"""

        torrents = [
            {
                "title": "Movie.2023.1080p.WEB-DL.x264",
                "seeders": 50,
                "size": 4 * 1024 * 1024 * 1024,  # 4GB
            },
            {
                "title": "Movie.2023.CAM.x264",  # Should be excluded
                "seeders": 100,
                "size": 1 * 1024 * 1024 * 1024,  # 1GB
            },
            {
                "title": "Movie.2023.720p.WEB-DL.x264",  # Wrong quality
                "seeders": 30,
                "size": 3 * 1024 * 1024 * 1024,  # 3GB
            },
            {
                "title": "Movie.2023.1080p.BluRay.x264",
                "seeders": 25,
                "size": 5 * 1024 * 1024 * 1024,  # 5GB
            }
        ]

        filtered = jackett_client.filter_torrents(torrents)

        # Should only have the first and last torrents
        assert len(filtered) == 2
        assert "WEB-DL" in filtered[0]["title"] or "BluRay" in filtered[0]["title"]
        assert all(t["seeders"] >= 20 for t in filtered)

    def test_calculate_score(self, jackett_client):
        """Test torrent scoring algorithm"""

        web_dl_torrent = {
            "title": "Movie.2023.1080p.WEB-DL.x264",
            "seeders": 50,
            "size": 4 * 1024 * 1024 * 1024,  # 4GB (optimal size)
            "downloadvolumefactor": 0.0,  # Freeleech
        }

        bluray_torrent = {
            "title": "Movie.2023.1080p.BluRay.x264",
            "seeders": 30,
            "size": 6 * 1024 * 1024 * 1024,  # 6GB
            "downloadvolumefactor": 1.0,
        }

        web_dl_score = jackett_client._calculate_score(web_dl_torrent)
        bluray_score = jackett_client._calculate_score(bluray_torrent)

        # WEB-DL with freeleech should score higher
        assert web_dl_score > bluray_score

    @pytest.mark.asyncio
    async def test_get_best_torrent_success(self, jackett_client):
        """Test getting the best torrent for a movie"""

        mock_torrents = [
            {
                "title": "Movie.2023.1080p.WEB-DL.x264",
                "seeders": 50,
                "size": 4 * 1024 * 1024 * 1024,
                "download_url": "http://test.com/download/123"
            }
        ]

        # Add score to mock torrents
        mock_torrents_with_score = [
            {
                "title": "Movie.2023.1080p.WEB-DL.x264",
                "seeders": 50,
                "size": 4 * 1024 * 1024 * 1024,
                "download_url": "http://test.com/download/123",
                "score": 25.0
            }
        ]

        with patch.object(jackett_client, 'search_torrents', return_value=mock_torrents):
            with patch.object(jackett_client, 'filter_torrents', return_value=mock_torrents_with_score):

                result = await jackett_client.get_best_torrent("Movie", 2023)

                assert result is not None
                assert result["title"] == "Movie.2023.1080p.WEB-DL.x264"

    @pytest.mark.asyncio
    async def test_get_best_torrent_no_results(self, jackett_client):
        """Test behavior when no torrents are found"""

        with patch.object(jackett_client, 'search_torrents', return_value=[]):

            result = await jackett_client.get_best_torrent("Nonexistent Movie", 2023)

            assert result is None


class TestBlackholeClient:

    @pytest.fixture
    def blackhole_client(self):
        with patch('src.app.blackhole.settings') as mock_settings:
            mock_settings.autoadd_watch_dir = "/tmp/test-blackhole"
            return BlackholeClient()

    def test_generate_filename(self, blackhole_client):
        """Test filename generation for torrent files"""

        title = "Movie Title (2023) 1080p WEB-DL x264-GROUP"
        filename = blackhole_client._generate_filename(title)

        assert filename.endswith(".torrent")
        assert "Movie Title" in filename
        assert len(filename) < 250  # Reasonable length

    def test_is_valid_torrent(self, blackhole_client):
        """Test torrent file validation"""

        # Valid torrent-like content
        valid_content = b'd8:announce9:test:test4:infod4:name9:test.file12:piece lengthi32768e6:pieces0:ee'
        assert blackhole_client._is_valid_torrent(valid_content)

        # Invalid content
        invalid_content = b'not a torrent file'
        assert not blackhole_client._is_valid_torrent(invalid_content)

    @pytest.mark.asyncio
    async def test_download_torrent(self, blackhole_client):
        """Test downloading and saving torrent file"""

        torrent_data = {
            "title": "Test Movie 2023 1080p WEB-DL",
            "download_url": "http://test.com/download/123.torrent"
        }

        mock_torrent_content = b'd8:announce9:test:test4:infod4:name9:test.file12:piece lengthi32768e6:pieces0:ee'

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.content = mock_torrent_content
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', create=True):

                    result = await blackhole_client.download_torrent(torrent_data)

                    assert result["filename"].endswith(".torrent")
                    assert result["size"] == len(mock_torrent_content)
                    assert "Test Movie" in result["filename"]

    @pytest.mark.asyncio
    async def test_grab_via_blackhole(self, blackhole_client):
        """Test complete blackhole workflow"""

        mock_torrent = {
            "title": "Test Movie 2023 1080p WEB-DL",
            "download_url": "http://test.com/download/123.torrent",
            "seeders": 50,
            "size": 4 * 1024 * 1024 * 1024
        }

        mock_download_result = {
            "filename": "test_movie.torrent",
            "path": "/tmp/test-blackhole/test_movie.torrent",
            "size": 1024
        }

        with patch('src.app.jackett.jackett_client') as mock_jackett:
            mock_jackett.get_best_torrent = AsyncMock(return_value=mock_torrent)

            with patch.object(blackhole_client, 'download_torrent', return_value=mock_download_result):

                result = await blackhole_client.grab_via_blackhole("Test Movie", 2023)

                assert result["method"] == "blackhole"
                assert result["title"] == "Test Movie"
                assert result["year"] == 2023
                assert result["torrent"] == mock_torrent
                assert result["download"] == mock_download_result

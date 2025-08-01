from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import json
import pytz

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Channel configurations
CHANNELS = [
    {"id": "hbo", "name": "HBO", "url_name": "hbo"},
    {"id": "hbo2", "name": "HBO 2", "url_name": "hbo2"},
    {"id": "hbo_signature", "name": "HBO Signature", "url_name": "hbo-signature"},
    {"id": "hbo_family", "name": "HBO Family", "url_name": "hbo-family"},
    {"id": "hbo_comedy", "name": "HBO Comedy", "url_name": "hbo-comedy"},
    {"id": "hbo_zone", "name": "HBO Zone", "url_name": "hbo-zone"},
    {"id": "cinemax", "name": "Cinemax", "url_name": "cinemax"},
    {"id": "more_max", "name": "More MAX", "url_name": "more-max"},
    {"id": "action_max", "name": "Action MAX", "url_name": "action-max"},
    {"id": "thriller_max", "name": "Thriller MAX", "url_name": "thrillermax"},
    {"id": "5star_max", "name": "5 Star MAX", "url_name": "5-star-max"},
    {"id": "movie_max", "name": "Movie MAX", "url_name": "moviemax"},
    {"id": "outer_max", "name": "Outer MAX", "url_name": "outer-max"},
    {"id": "showtime", "name": "Showtime", "url_name": "showtime"},
    {"id": "showtime2", "name": "Showtime 2", "url_name": "showtime-2"},
    {"id": "shoxbet", "name": "SHOxBET", "url_name": "shoxbet"},
    {"id": "showtime_extreme", "name": "Showtime Extreme", "url_name": "showtime-extreme"},
    {"id": "showtime_next", "name": "Showtime Next", "url_name": "showtime-next"},
    {"id": "showtime_women", "name": "Showtime Women", "url_name": "showtime-women"},
    {"id": "showtime_family", "name": "Showtime Family Zone", "url_name": "showtime-familyzone"},
    {"id": "showtime_showcase", "name": "Showtime Showcase", "url_name": "showtime-showcase"},
    {"id": "starz", "name": "Starz", "url_name": "starz"},
    {"id": "starz_edge", "name": "Starz Edge", "url_name": "starz-edge"},
    {"id": "starz_black", "name": "Starz in Black", "url_name": "starz-in-black"},
    {"id": "starz_comedy", "name": "Starz Comedy", "url_name": "starz-comedy"},
    {"id": "starz_cinema", "name": "Starz Cinema", "url_name": "starz-cinema"},
    {"id": "starz_kids", "name": "Starz Kids & Family", "url_name": "starz-kids-family"},
    {"id": "starz_encore", "name": "Starz Encore", "url_name": "starz-encore"},
    {"id": "starz_encore_action", "name": "Starz Encore Action", "url_name": "starz-encore-action"},
    {"id": "starz_encore_classic", "name": "Starz Encore Classic", "url_name": "starz-encore-classic"},
    {"id": "starz_encore_black", "name": "Starz Encore Black", "url_name": "starz-encore-black"},
    {"id": "starz_encore_family", "name": "Starz Encore Family", "url_name": "starz-encore-family"},
    {"id": "starz_encore_suspense", "name": "Starz Encore Suspense", "url_name": "starz-encore-suspense"},
    {"id": "starz_encore_westerns", "name": "Starz Encore Westerns", "url_name": "starz-encore-westerns"},
    {"id": "tnt", "name": "TNT", "url_name": "tnt"},
    {"id": "syfy", "name": "SYFY", "url_name": "syfy"},
    {"id": "amc", "name": "AMC", "url_name": "amc"},
    {"id": "fx", "name": "FX", "url_name": "fx"},
    {"id": "fx_movie", "name": "FX Movie Channel", "url_name": "fx-movie-channel"},
    {"id": "fxx", "name": "FXX", "url_name": "fxx"},
    {"id": "bbc_america", "name": "BBC America", "url_name": "bbc-america"},
    {"id": "bounce_tv", "name": "Bounce TV", "url_name": "bounce-tv"},
    {"id": "cartoon", "name": "Cartoon Network", "url_name": "cartoon-network"},
    {"id": "court_tv", "name": "Court TV", "url_name": "court-tv"},
    {"id": "freeform", "name": "Freeform", "url_name": "freeform"},
    {"id": "heroes_icons", "name": "Heroes & Icons", "url_name": "heroes-icons"},
    {"id": "ion_mystery", "name": "ION Mystery", "url_name": "ion-mystery"},
    {"id": "metv", "name": "MeTV", "url_name": "metv"},
    {"id": "metv_toons", "name": "MeTV Toons", "url_name": "metv-toons"},
    {"id": "mgm_plus", "name": "MGM+", "url_name": "mgm-plus"},
    {"id": "vh1", "name": "VH1", "url_name": "vh1"},
    {"id": "vice_tv", "name": "Vice TV", "url_name": "vice-tv"}
]

# Define Models
class Show(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    show_type: str  # "Series" or "Feature Film" or "Sports"
    year: Optional[str] = None
    season: Optional[str] = None
    episode: Optional[str] = None
    episode_title: Optional[str] = None
    description: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    duration: Optional[int] = None  # in minutes
    genre: Optional[str] = None
    channel_id: str
    date: str  # YYYY-MM-DD format
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChannelSchedule(BaseModel):
    channel_id: str
    channel_name: str
    date: str
    shows: List[Show]

class ScheduleResponse(BaseModel):
    channels: List[ChannelSchedule]
    current_time: str
    timezone: str = "America/New_York"

async def scrape_channel_schedule(session: aiohttp.ClientSession, channel: Dict[str, str], target_date: str = None) -> List[Show]:
    """Scrape schedule for a specific channel"""
    if target_date is None:
        target_date = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d')
    
    url = f"https://www.tvinsider.com/network/{channel['url_name']}/schedule/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                logging.error(f"Failed to fetch {channel['name']} schedule: {response.status}")
                return []
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            shows = []
            
            # Find all show containers
            show_containers = soup.find_all('a', class_='show-upcoming')
            
            for container in show_containers:
                try:
                    # Extract time
                    time_elem = container.find('time')
                    if not time_elem:
                        continue
                    start_time = time_elem.get_text(strip=True)
                    
                    # Extract title
                    title_elem = container.find('h3')
                    if not title_elem:
                        continue
                    title_text = title_elem.get_text(strip=True)
                    
                    # Remove "New" indicator if present
                    title = title_text.replace(' New', '') if ' New' in title_text else title_text
                    
                    # Extract show type and year
                    type_elem = container.find('h4')
                    show_type = "Unknown"
                    year = None
                    if type_elem:
                        type_text = type_elem.get_text(strip=True)
                        if '•' in type_text:
                            parts = type_text.split('•')
                            show_type = parts[0].strip()
                            if len(parts) > 1:
                                year = parts[1].strip()
                    
                    # Extract episode info
                    episode_title = None
                    season = None
                    episode = None
                    
                    episode_title_elem = container.find('h5')
                    if episode_title_elem:
                        episode_title = episode_title_elem.get_text(strip=True)
                    
                    season_episode_elem = container.find('h6')
                    if season_episode_elem:
                        se_text = season_episode_elem.get_text(strip=True)
                        # Parse "Season X • Episode Y"
                        if 'Season' in se_text and 'Episode' in se_text:
                            match = re.search(r'Season (\d+).*Episode (\d+)', se_text)
                            if match:
                                season = f"Season {match.group(1)}"
                                episode = f"Episode {match.group(2)}"
                    
                    # Extract description
                    description = None
                    desc_elem = container.find('p')
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                    
                    show = Show(
                        title=title,
                        show_type=show_type,
                        year=year,
                        season=season,
                        episode=episode,
                        episode_title=episode_title,
                        description=description,
                        start_time=start_time,
                        channel_id=channel['id'],
                        date=target_date
                    )
                    
                    shows.append(show)
                    
                except Exception as e:
                    logging.error(f"Error parsing show for {channel['name']}: {str(e)}")
                    continue
            
            logging.info(f"Scraped {len(shows)} shows for {channel['name']}")
            return shows
            
    except Exception as e:
        logging.error(f"Error scraping {channel['name']}: {str(e)}")
        return []

@api_router.get("/")
async def root():
    return {"message": "TV Schedule API"}

@api_router.get("/channels")
async def get_channels():
    """Get list of all available channels"""
    return {"channels": CHANNELS}

@api_router.get("/schedule", response_model=ScheduleResponse)
async def get_schedule(date: Optional[str] = None):
    """Get schedule for all channels"""
    try:
        # Use current date if none provided
        if date is None:
            et_tz = pytz.timezone('America/New_York')
            target_date = datetime.now(et_tz).strftime('%Y-%m-%d')
        else:
            target_date = date
        
        # Create aiohttp session
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Scrape all channels concurrently (but limit concurrency)
            semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
            
            async def scrape_with_semaphore(channel):
                async with semaphore:
                    return await scrape_channel_schedule(session, channel, target_date)
            
            # Scrape first 10 channels initially for quick response
            priority_channels = CHANNELS[:10]
            tasks = [scrape_with_semaphore(channel) for channel in priority_channels]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Build response
            channels_data = []
            
            for i, channel in enumerate(priority_channels):
                shows_data = results[i] if not isinstance(results[i], Exception) else []
                
                channel_schedule = ChannelSchedule(
                    channel_id=channel['id'],
                    channel_name=channel['name'],
                    date=target_date,
                    shows=shows_data
                )
                channels_data.append(channel_schedule)
            
            # Get current time in ET
            et_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(et_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            return ScheduleResponse(
                channels=channels_data,
                current_time=current_time,
                timezone="America/New_York"
            )
            
    except Exception as e:
        logging.error(f"Error getting schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/schedule/{channel_id}")
async def get_channel_schedule(channel_id: str, date: Optional[str] = None):
    """Get schedule for a specific channel"""
    try:
        # Find channel
        channel = next((c for c in CHANNELS if c['id'] == channel_id), None)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Use current date if none provided
        if date is None:
            et_tz = pytz.timezone('America/New_York')
            target_date = datetime.now(et_tz).strftime('%Y-%m-%d')
        else:
            target_date = date
        
        # Create aiohttp session and scrape
        connector = aiohttp.TCPConnector(limit=1)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            shows = await scrape_channel_schedule(session, channel, target_date)
            
            return ChannelSchedule(
                channel_id=channel['id'],
                channel_name=channel['name'],
                date=target_date,
                shows=shows
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting channel schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/refresh")
async def refresh_schedule():
    """Manually refresh the schedule data"""
    try:
        # This endpoint can be used to trigger a manual refresh
        # For now, it just returns success
        return {"message": "Schedule refresh initiated", "status": "success"}
    except Exception as e:
        logging.error(f"Error refreshing schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
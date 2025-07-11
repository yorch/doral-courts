import sqlite3
from typing import List, Optional
from datetime import datetime
from scraper import Court
from logger import get_logger

logger = get_logger(__name__)

class DoralCourtsDB:
    def __init__(self, db_path: str = "doral_courts.db"):
        self.db_path = db_path
        logger.debug("Initializing database at path: %s", db_path)
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        logger.debug("Setting up database schema")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS courts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sport_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    surface_type TEXT NOT NULL,
                    availability_status TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    price TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, date, time_slot)
                )
            ''')
            logger.debug("Created courts table")
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sport_type 
                ON courts(sport_type)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_availability 
                ON courts(availability_status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_date 
                ON courts(date)
            ''')
            logger.debug("Created database indexes")
            
            conn.commit()
        
        logger.info("Database initialized successfully")

    def insert_courts(self, courts: List[Court]) -> int:
        """Insert or update court data in the database."""
        logger.info("Inserting %d courts into database", len(courts))
        inserted_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for i, court in enumerate(courts):
                try:
                    logger.debug("Inserting court %d/%d: %s", i + 1, len(courts), court.name)
                    cursor.execute('''
                        INSERT OR REPLACE INTO courts 
                        (name, sport_type, location, surface_type, availability_status, 
                         date, time_slot, price, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        court.name,
                        court.sport_type,
                        court.location,
                        court.surface_type,
                        court.availability_status,
                        court.date,
                        court.time_slot,
                        court.price
                    ))
                    inserted_count += 1
                except sqlite3.Error as e:
                    logger.error("Error inserting court %s: %s", court.name, e)
                    
            conn.commit()
            
        logger.info("Successfully inserted/updated %d courts", inserted_count)
        return inserted_count

    def get_courts(
        self, 
        sport_type: Optional[str] = None,
        availability_status: Optional[str] = None,
        date: Optional[str] = None
    ) -> List[Court]:
        """Retrieve courts from the database with optional filters."""
        logger.debug("Querying courts with filters - Sport: %s, Status: %s, Date: %s", 
                    sport_type, availability_status, date)
        
        query = "SELECT name, sport_type, location, surface_type, availability_status, date, time_slot, price FROM courts WHERE 1=1"
        params = []
        
        if sport_type:
            query += " AND sport_type = ?"
            params.append(sport_type)
            
        if availability_status:
            query += " AND availability_status = ?"
            params.append(availability_status)
            
        if date:
            query += " AND date = ?"
            params.append(date)
            
        query += " ORDER BY date, time_slot, sport_type, name"
        
        logger.debug("Executing query: %s with params: %s", query, params)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
        logger.debug("Query returned %d rows", len(rows))
        
        courts = []
        for i, row in enumerate(rows):
            court = Court(
                name=row[0],
                sport_type=row[1],
                location=row[2],
                surface_type=row[3],
                availability_status=row[4],
                date=row[5],
                time_slot=row[6],
                price=row[7]
            )
            courts.append(court)
            logger.debug("Loaded court %d: %s", i + 1, court.name)
            
        logger.info("Retrieved %d courts from database", len(courts))
        return courts

    def clear_old_data(self, days_old: int = 7):
        """Remove court data older than specified days."""
        logger.info("Clearing data older than %d days", days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # First count how many will be deleted
            cursor.execute('''
                SELECT COUNT(*) FROM courts 
                WHERE last_updated < datetime('now', '-' || ? || ' days')
            ''', (days_old,))
            count_to_delete = cursor.fetchone()[0]
            logger.debug("Found %d records to delete", count_to_delete)
            
            cursor.execute('''
                DELETE FROM courts 
                WHERE last_updated < datetime('now', '-' || ? || ' days')
            ''', (days_old,))
            conn.commit()
            
        logger.info("Deleted %d old records", count_to_delete)
            
    def get_stats(self) -> dict:
        """Get database statistics."""
        logger.debug("Generating database statistics")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM courts")
            total_courts = cursor.fetchone()[0]
            logger.debug("Total courts in database: %d", total_courts)
            
            cursor.execute("SELECT sport_type, COUNT(*) FROM courts GROUP BY sport_type")
            sport_counts = dict(cursor.fetchall())
            logger.debug("Sport breakdown: %s", sport_counts)
            
            cursor.execute("SELECT availability_status, COUNT(*) FROM courts GROUP BY availability_status")
            availability_counts = dict(cursor.fetchall())
            logger.debug("Availability breakdown: %s", availability_counts)
            
            cursor.execute("SELECT MAX(last_updated) FROM courts")
            last_update = cursor.fetchone()[0]
            logger.debug("Last update: %s", last_update)
            
        stats = {
            'total_courts': total_courts,
            'sport_counts': sport_counts,
            'availability_counts': availability_counts,
            'last_updated': last_update
        }
        
        logger.info("Generated database statistics")
        return stats
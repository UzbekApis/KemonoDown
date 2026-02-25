"""
Script to update ZIP file URLs for old downloads
"""
import sqlite3
import os
from api.kemono_client import KemonoAPIClient

def update_zip_urls():
    db_path = "data/webapp.db"
    
    if not os.path.exists(db_path):
        print("Database not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all ZIP files without original_url
        cursor.execute("""
            SELECT id, filename, service, user_id, post_id
            FROM files
            WHERE file_type = 'archive' AND (original_url IS NULL OR original_url = '')
        """)
        
        zip_files = cursor.fetchall()
        
        if not zip_files:
            print("No ZIP files without URLs found.")
            return
        
        print(f"Found {len(zip_files)} ZIP files without URLs")
        
        api_client = KemonoAPIClient()
        updated_count = 0
        
        # Group by post_id to minimize API calls
        posts_cache = {}
        
        for file_id, filename, service, user_id, post_id in zip_files:
            if not service or not user_id or not post_id:
                print(f"Skipping {filename}: missing service/user_id/post_id")
                continue
            
            # Get post data from cache or API
            cache_key = f"{service}_{user_id}_{post_id}"
            if cache_key not in posts_cache:
                try:
                    print(f"Fetching post data for {service}/{user_id}/{post_id}...")
                    post_data = api_client.get_post_details(service, user_id, post_id)
                    posts_cache[cache_key] = post_data
                except Exception as e:
                    print(f"Error fetching post {post_id}: {e}")
                    posts_cache[cache_key] = None
                    continue
            
            post_data = posts_cache[cache_key]
            if not post_data:
                continue
            
            # Find matching attachment
            attachments = post_data.get('attachments', [])
            for attachment in attachments:
                att_name = attachment.get('name', '')
                att_path = attachment.get('path', '')
                
                if att_name == filename or att_path.endswith(filename):
                    # Found match, update URL
                    url = f"https://kemono.cr/data{att_path}"
                    cursor.execute("""
                        UPDATE files SET original_url = ? WHERE id = ?
                    """, (url, file_id))
                    conn.commit()
                    print(f"Updated {filename}: {url}")
                    updated_count += 1
                    break
        
        print(f"\nUpdated {updated_count} ZIP file URLs")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_zip_urls()

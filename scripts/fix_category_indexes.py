#!/usr/bin/env python3
"""
Script to fix MongoDB index conflicts for the categories collection.
This script will drop the conflicting index and allow the application to recreate it properly.
"""

import pymongo
import os
from pymongo import MongoClient

def fix_category_indexes():
    """Fix category index conflicts by dropping and recreating them properly."""
    
    # Get MongoDB connection details from environment or use defaults
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "marketplace")
    
    try:
        print(f"Connecting to MongoDB: {mongo_uri}")
        client = MongoClient(mongo_uri)
        db = client[database_name]
        collection = db["categories"]
        
        print("Current indexes:")
        for index in collection.list_indexes():
            print(f"  - {index}")
        
        # Drop the conflicting index if it exists
        try:
            print("\nDropping conflicting 'category_name_1' index...")
            collection.drop_index("category_name_1")
            print("✅ Successfully dropped conflicting index")
        except pymongo.errors.OperationFailure as e:
            if "index not found" in str(e).lower():
                print("ℹ️  Index 'category_name_1' not found, no need to drop")
            else:
                print(f"⚠️  Error dropping index: {e}")
        
        # Create the new indexes with specific names
        try:
            print("\nCreating new indexes...")
            
            # Create unique index on category_name
            collection.create_index(
                [("category_name", pymongo.ASCENDING)], 
                unique=True, 
                name="categories_name_unique"
            )
            print("✅ Created unique index on category_name")
            
            # Create index on parent_category
            collection.create_index(
                [("parent_category", pymongo.ASCENDING)], 
                name="categories_parent_category"
            )
            print("✅ Created index on parent_category")
            
        except pymongo.errors.OperationFailure as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Indexes already exist with correct names")
            else:
                print(f"⚠️  Error creating indexes: {e}")
        
        print("\nFinal indexes:")
        for index in collection.list_indexes():
            print(f"  - {index}")
            
        print("\n✅ Index fix completed successfully!")
        print("You can now restart your application.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your MongoDB connection and try again.")

if __name__ == "__main__":
    fix_category_indexes() 
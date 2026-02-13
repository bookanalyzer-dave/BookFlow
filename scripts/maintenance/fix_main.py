#!/usr/bin/env python3
"""Script to fix the book_data extraction logic in main.py"""

def fix_main_py():
    filepath = 'agents/ingestion-agent/main.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the problematic section
    old_code = '''        grounding_metadata = extract_grounding_metadata(response)
        
        book_data = None
        book_data_dict = find_and_extract_book_data(result_json)
        
        logger.info(f"🔍 find_and_extract_book_data returned: {book_data_dict is not None}")
        if book_data_dict:
            logger.info(f"📚 Extracted book_data keys: {list(book_data_dict.keys())}")
        else:
            logger.warning(f"⚠️ find_and_extract_book_data returned None! Checking result_json structure...")
            logger.warning(f"⚠️ result_json type: {type(result_json)}")
            if isinstance(result_json, dict):
                logger.warning(f"⚠️ result_json keys: {list(result_json.keys())}")
                for key in result_json.keys():
                    logger.warning(f"⚠️ result_json['{key}'] type: {type(result_json[key])}")
        
        if book_data_dict:
            print(f"!!! Buchdaten gefunden: {list(book_data_dict.keys())}")
            if "metadata" not in book_data_dict:
                book_data_dict["metadata"] = {}
            book_data_dict["metadata"]["raw_gemini_response"] = result_json
            try:
                book_data = BookData(**book_data_dict)
            except Exception as ve:
                print(f"!!! BookData Validation Error: {ve}")'''
    
    new_code = '''        grounding_metadata = extract_grounding_metadata(response)
        
        # Gemini liefert bereits das korrekte Format direkt, nutze es
        book_data = None
        book_data_dict = result_json.get("book_data") if isinstance(result_json, dict) else None
        
        logger.info(f"🔍 Extracted book_data from result_json: {book_data_dict is not None}")
        if book_data_dict and isinstance(book_data_dict, dict):
            logger.info(f"📚 book_data keys: {list(book_data_dict.keys())}")
            print(f"!!! Buchdaten gefunden: {list(book_data_dict.keys())}")
            if "metadata" not in book_data_dict:
                book_data_dict["metadata"] = {}
            book_data_dict["metadata"]["raw_gemini_response"] = result_json
            try:
                book_data = BookData(**book_data_dict)
                logger.info(f"✅ BookData successfully created with title: {book_data.title}")
            except Exception as ve:
                print(f"!!! BookData Validation Error: {ve}")
                logger.error(f"❌ BookData Validation Error: {ve}", exc_info=True)
        else:
            logger.warning(f"⚠️ No valid book_data in result_json!")
            if isinstance(result_json, dict):
                logger.warning(f"⚠️ result_json keys: {list(result_json.keys())}")'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Replaced book_data extraction logic")
    else:
        print("⚠️ Could not find exact match for old code")
        return False
    
    # Update version marker
    content = content.replace(
        'VERSION MARKER: v2.23-NO-TOOLS-JSON-ONLY',
        'VERSION MARKER: v2.24-DIRECT-BOOK-DATA'
    )
    print("✅ Updated version marker")
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Successfully updated {filepath}")
    return True

if __name__ == '__main__':
    success = fix_main_py()
    exit(0 if success else 1)

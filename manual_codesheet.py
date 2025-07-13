import pandas as pd
import re
import os
import subprocess
import platform
from pathlib import Path
from dateutil.parser import parse as _dt_parse

def parse_single_date(text):
    """Return ISO date ('YYYY-MM-DD') if text looks like a date."""
    try:
        clean = text.strip().rstrip('.')
        dt = _dt_parse(clean, fuzzy=True)
        return dt.date().isoformat()
    except (ValueError, OverflowError):
        return None

def extract_countries(text):
    """Return a semicolon-separated string of CountryName(code) pairs found in text."""
    pairs = []
    
    # Pattern A – code first, then name (e.g. "365 Russia 200 United Kingdom.")
    for code, name in re.findall(
        r'\b(\d{3})\s+([A-Z][A-Za-z.\- ]+?)'
        r'(?='
          r'(?:\s+\d{3}\s)'
          r'|[.,;\n]'
          r'|$'
        r')',
        text
    ):
        pair = f"{name.strip()}({code})"
        if pair not in pairs:
            pairs.append(pair)
    
    # Pattern B – name first, then code in parentheses (e.g. "Russia (365)")
    for name, code in re.findall(
        r'\b([A-Z][A-Za-z.\- ]+?)\s*\(\s*(\d{3})\s*\)',
        text
    ):
        pair = f"{name.strip()}({code})"
        if pair not in pairs:
            pairs.append(pair)
    
    return ";".join(pairs)

def categorize_answer(answer_text):
    """Categorize the answer based on its content"""
    answer_clean = answer_text.strip()
    
    # Check for Yes/No answers
    if answer_clean.lower() in ['yes', 'no', 'yes.', 'no.', 'n/a', 'n/a.', 'zero', 'zero.']:
        return "Yes/No+Text"
    
    # Check for coded list answers (contains semicolons or specific patterns)
    if ';' in answer_clean and len(answer_clean) < 100:
        return "Coded_List"
    
    # Check for multiple items (contains "and" or comma-separated short items)
    if (',' in answer_clean or ' and ' in answer_clean.lower()) and len(answer_clean) < 100:
        return "Multiple"
    
    # Check for numeric answers
    if re.match(r'^\d+\.?$', answer_clean):
        return "Numeric"
    
    # Default to text for longer answers
    return "Text"

def open_source_file(filename, base_path="atop_version_5.1_codesheets/ATOP Version 5.1 Codesheets/"):
    """
    Open the source PDF file using system default application.
    
    Args:
        filename (str): The source filename (e.g., ATOP1350.1.pdf)
        base_path (str): Base directory where PDF files are stored
    
    Returns:
        bool: True if file was opened successfully, False otherwise
    """
    if pd.isna(filename) or not filename or filename == "Unknown":
        print("❌ No source filename available")
        return False
    
    # Construct full path
    full_path = Path(base_path) / filename
    
    if not full_path.exists():
        print(f"❌ File not found: {full_path}")
        # Try without base path (in case it's in current directory)
        if Path(filename).exists():
            full_path = Path(filename)
        else:
            return False
    
    try:
        # Open file with system default application
        system = platform.system().lower()
        
        if system == "windows":
            os.startfile(str(full_path))
        elif system == "darwin":  # macOS
            subprocess.run(["open", str(full_path)])
        else:  # Linux and others
            subprocess.run(["xdg-open", str(full_path)])
        
        print(f"📂 Opened: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error opening file: {e}")
        return False

def update_record_fields(df, record_index, new_answer_text, question_id):
    """Update all derived fields based on new answer text"""
    
    # Clean the new answer text
    cleaned_answer = new_answer_text.replace('\n', ' ').replace('\r', '').strip()
    cleaned_answer = re.sub(r'\s+', ' ', cleaned_answer)
    
    old_answer = df.loc[record_index, 'Answer_Text']
    
    # Update Answer_Text
    df.at[record_index, 'Answer_Text'] = cleaned_answer
    
    # Update Text_Length
    df.at[record_index, 'Text_Length'] = len(cleaned_answer)
    
    # Update Answer_YesNo
    low = cleaned_answer.lower()
    if low.startswith("yes"):
        df.at[record_index, 'Answer_YesNo'] = "Yes"
    elif low.startswith("no"):
        df.at[record_index, 'Answer_YesNo'] = "No"
    else:
        df.at[record_index, 'Answer_YesNo'] = "N/A"
    
    # Update Decoded_Countries
    decoded = extract_countries(cleaned_answer)
    df.at[record_index, 'Decoded_Countries'] = decoded
    
    # Update Answer_Category (with special handling for Q3/Q14)
    if question_id in ("Q3", "Q14"):
        iso = parse_single_date(cleaned_answer)
        if iso:
            df.at[record_index, 'Answer_Text'] = iso
            df.at[record_index, 'Text_Length'] = len(iso)
            cleaned_answer = iso
        df.at[record_index, 'Answer_Category'] = "Date"
    else:
        if decoded:
            df.at[record_index, 'Answer_Category'] = "coded_text"
        else:
            df.at[record_index, 'Answer_Category'] = categorize_answer(cleaned_answer)
    
    return old_answer, cleaned_answer

def find_record_in_main_dataset(main_df, alliance_id, question_id):
    """Find record in main dataset by Alliance_ID and Question_ID"""
    
    # Convert alliance_id to string for consistent comparison
    alliance_id_str = str(alliance_id).strip()
    
    # Search for the record
    mask = (main_df['Alliance_ID'].astype(str).str.strip() == alliance_id_str) & (main_df['Question_ID'] == question_id)
    matching_records = main_df[mask]
    
    if len(matching_records) == 0:
        return None, f"No record found for Alliance {alliance_id}, {question_id}"
    elif len(matching_records) > 1:
        return None, f"Multiple records found for Alliance {alliance_id}, {question_id} ({len(matching_records)} matches)"
    else:
        return matching_records.index[0], "Found"

def get_valid_choice(prompt, valid_choices):
    """Get valid input with retry loop"""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        else:
            valid_str = "', '".join(valid_choices)
            print(f"❓ Invalid choice! Please enter '{valid_str}'")

def systematic_error_correction():
    """Systematic error correction using doublecheck.csv as guide"""
    
    print("🔧 ATOP Systematic Error Correction")
    print("=" * 50)
    print("Features:")
    print("  • Automatically opens source PDF files")
    print("  • Saves progress after each correction")
    print("  • Resume from where you left off")
    print("  • Input validation with retry")
    print()
    
    # Configuration
    pdf_base_path = input("📁 PDF files directory (or Enter for default): ").strip()
    if not pdf_base_path:
        pdf_base_path = "atop_version_5.1_codesheets/ATOP Version 5.1 Codesheets/"
    print(f"✅ Using PDF path: {pdf_base_path}")
    print()
    
    # File paths
    doublecheck_path = "doublecheck.csv"
    main_dataset_path = "ATOP_treaty_text_20250703.csv"
    
    # Load datasets
    try:
        print(f"📁 Loading doublecheck list: {doublecheck_path}")
        doublecheck_df = pd.read_csv(doublecheck_path)
        
        # Add resolved column if it doesn't exist
        if 'resolved' not in doublecheck_df.columns:
            doublecheck_df['resolved'] = 0
            print("✅ Added 'resolved' column to doublecheck.csv")
        
        print(f"✅ Loaded {len(doublecheck_df)} records to check")
        
    except Exception as e:
        print(f"❌ Error loading doublecheck.csv: {e}")
        return
    
    try:
        print(f"📁 Loading main dataset: {main_dataset_path}")
        main_df = pd.read_csv(main_dataset_path)
        print(f"✅ Loaded main dataset: {len(main_df):,} records")
        
    except Exception as e:
        print(f"❌ Error loading main dataset: {e}")
        return
    
    # Filter unresolved records
    unresolved = doublecheck_df[doublecheck_df['resolved'] == 0]
    print(f"📋 Found {len(unresolved)} unresolved records to process")
    
    if len(unresolved) == 0:
        print("🎉 All records have been resolved!")
        return
    
    corrections_made = 0
    opened_files = set()  # Track which files we've already opened
    
    for idx, check_record in unresolved.iterrows():
        alliance_id = check_record['Alliance_ID']
        question_id = check_record['Question_ID']
        
        print(f"\n" + "=" * 60)
        print(f"📋 RECORD {idx + 1}/{len(doublecheck_df)}: Alliance {alliance_id}, {question_id}")
        print("=" * 60)
        
        # Find corresponding record in main dataset
        record_index, status = find_record_in_main_dataset(main_df, alliance_id, question_id)
        
        if record_index is None:
            print(f"❌ {status}")
            
            # Mark as resolved (can't find it)
            doublecheck_df.at[idx, 'resolved'] = 1
            
            skip_choice = get_valid_choice("⏭️  Skip this record? (y/n): ", ['y', 'yes', 'n', 'no'])
            if skip_choice in ['y', 'yes']:
                continue
            else:
                continue
        
        # Show current record details
        current_record = main_df.loc[record_index]
        
        print(f"📄 CURRENT RECORD:")
        print(f"   Alliance ID:       {current_record['Alliance_ID']}")
        print(f"   Alliance Name:     {current_record['Alliance_Name']}")
        print(f"   Question:          {current_record['Question_Short']}")
        print(f"   Full Question:     {current_record['Question_Full']}")
        print(f"   Source File:       {current_record.get('Source_Filename', 'N/A')}")
        print(f"   Current Answer:    \"{current_record['Answer_Text']}\"")
        print(f"   Answer Category:   {current_record['Answer_Category']}")
        print(f"   Answer Yes/No:     {current_record['Answer_YesNo']}")
        print(f"   Text Length:       {current_record['Text_Length']}")
        print(f"   Decoded Countries: {current_record.get('Decoded_Countries', 'N/A')}")
        
        # Open source file if not already opened
        source_filename = current_record.get('Source_Filename', '')
        if source_filename and source_filename not in opened_files:
            print(f"\n📂 Opening source file: {source_filename}")
            if open_source_file(source_filename, pdf_base_path):
                opened_files.add(source_filename)
        
        # Ask if user wants to edit (with retry loop for valid input)
        edit_choice = get_valid_choice(f"\n✏️  Edit this record? (y/n/quit): ", ['y', 'yes', 'n', 'no', 'quit'])
        
        if edit_choice == 'quit':
            print("🛑 Exiting...")
            break
        elif edit_choice in ['n', 'no']:
            print("⏭️  Skipping...")
            # Mark as resolved (user chose not to edit)
            doublecheck_df.at[idx, 'resolved'] = 1
        elif edit_choice in ['y', 'yes']:
            # Get new answer
            print(f"📝 Enter new answer (press Enter twice to finish):")
            answer_lines = []
            while True:
                line = input()
                if line == "" and answer_lines:  # Empty line and we have content
                    break
                elif line.lower() in ['quit', 'exit']:
                    print("🛑 Exiting...")
                    return
                answer_lines.append(line)
            
            if not answer_lines:
                print("   No answer provided, skipping...")
                continue
            
            # Join lines
            new_answer = ' '.join(answer_lines)
            
            # Update the record
            old_answer, cleaned_answer = update_record_fields(main_df, record_index, new_answer, question_id)
            
            # Show the change
            print(f"\n✅ UPDATED RECORD:")
            print(f"   OLD: \"{old_answer}\"")
            print(f"   NEW: \"{cleaned_answer}\"")
            print(f"   Category: {main_df.at[record_index, 'Answer_Category']}")
            print(f"   Yes/No: {main_df.at[record_index, 'Answer_YesNo']}")
            
            decoded = main_df.at[record_index, 'Decoded_Countries']
            if pd.notna(decoded) and decoded:
                print(f"   Countries: {decoded}")
            
            corrections_made += 1
            
            # Mark as resolved
            doublecheck_df.at[idx, 'resolved'] = 1
            
            # Save both datasets immediately
            try:
                main_df.to_csv(main_dataset_path, index=False)
                doublecheck_df.to_csv(doublecheck_path, index=False)
                print(f"💾 Saved both datasets (Correction #{corrections_made})")
            except Exception as e:
                print(f"❌ Save error: {e}")
        
        # Save progress on doublecheck.csv
        try:
            doublecheck_df.to_csv(doublecheck_path, index=False)
        except Exception as e:
            print(f"❌ Error saving doublecheck progress: {e}")
    
    # Final summary
    remaining_unresolved = len(doublecheck_df[doublecheck_df['resolved'] == 0])
    total_resolved = len(doublecheck_df[doublecheck_df['resolved'] == 1])
    
    print(f"\n" + "=" * 60)
    print(f"📊 SESSION SUMMARY")
    print("=" * 60)
    print(f"   Corrections made this session: {corrections_made}")
    print(f"   Total resolved records:        {total_resolved}")
    print(f"   Remaining unresolved:          {remaining_unresolved}")
    print(f"   Completion rate:               {total_resolved/len(doublecheck_df)*100:.1f}%")
    print(f"   Source files opened:           {len(opened_files)}")
    
    if opened_files:
        print(f"\n📂 Files opened this session:")
        for filename in sorted(opened_files):
            print(f"   • {filename}")
    
    if remaining_unresolved == 0:
        print(f"\n🎉 ALL RECORDS RESOLVED! Great job!")
    else:
        print(f"\n📝 {remaining_unresolved} records still need attention.")
        print(f"   Run the script again to continue where you left off.")

# Run the systematic error correction
if __name__ == "__main__":
    systematic_error_correction()
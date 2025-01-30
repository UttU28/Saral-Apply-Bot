import json
import os
from datetime import datetime

def readTheInputsFrom(htmlData):
    """
    Analyze the Easy Apply form HTML data and extract relevant information
    """
    from bs4 import BeautifulSoup

    print("Analyzing Easy Apply form data:")
    soup = BeautifulSoup(htmlData, 'html.parser')
    
    # Find all form elements
    form_elements = soup.find_all('div', class_='fb-dash-form-element')
    
    # Counter for questions
    question_count = 0
    questions = []
    
    # Analyze each form element
    for element in form_elements:
        # Determine input type
        input_type = "Unknown"
        question_text = ""
        
        # Check for checkbox fieldset first
        checkbox_fieldset = element.find('fieldset', attrs={'data-test-checkbox-form-component': 'true'})
        if checkbox_fieldset:
            input_type = "Multiple Select (Checkbox)"
            # Find the question text in the legend div
            legend_div = checkbox_fieldset.find('div', class_='fb-dash-form-element__label')
            if legend_div:
                # Get the text from the inner span that contains the question
                inner_span = legend_div.find('span', {'aria-hidden': 'true'})
                if inner_span:
                    question_text = inner_span.text.strip()
        
        # Check for radio button fieldset
        if not question_text:
            radio_fieldset = element.find('fieldset', attrs={'data-test-form-builder-radio-button-form-component': 'true'})
            if radio_fieldset:
                input_type = "Radio Button"
                # Find the question text in the legend span
                legend_span = radio_fieldset.find('span', class_='fb-dash-form-element__label')
                if legend_span:
                    # Get the text from the inner span that contains the question
                    inner_span = legend_span.find('span', {'aria-hidden': 'true'})
                    if inner_span:
                        question_text = inner_span.text.strip()
        
        # If not a radio button or checkbox, check other types
        if not question_text:
            select_element = element.find('select')
            if select_element:
                input_type = "Dropdown"
                label = element.find('label', class_='fb-dash-form-element__label')
                if label:
                    inner_span = label.find('span', {'aria-hidden': 'true'})
                    if inner_span:
                        question_text = inner_span.text.strip()
            elif element.find('input', attrs={'type': 'text'}):
                input_type = "Text Input"
            elif element.find('input', attrs={'type': 'email'}):
                input_type = "Email Input"
            elif element.find('input', attrs={'type': 'tel'}):
                input_type = "Phone Input"
            
            # Look for labels if question text not found yet
            if not question_text:
                label = element.find('label')
                if not label:
                    # Check for fieldset legend
                    legend = element.find('legend')
                    if legend:
                        label = legend.find('span', class_='fb-dash-form-element__label') or legend
                
                if label:
                    question_text = label.text.strip()
        
        if question_text:
            required = 'required' in str(element).lower() or 'aria-required="true"' in str(element)
            
            # Get options and current answer if available
            options = []
            current_answer = None
            
            if input_type in ["Multiple Select (Checkbox)", "Radio Button"]:
                option_labels = element.find_all('label', class_='t-14')
                options = [opt.text.strip() for opt in option_labels if opt.text.strip()]
                
                # Check for selected checkboxes/radio buttons
                selected_inputs = element.find_all('input', checked=True)
                if selected_inputs:
                    current_answer = [input.get('value') for input in selected_inputs]
                    # For radio buttons, convert single-item list to string
                    if input_type == "Radio Button" and current_answer:
                        current_answer = current_answer[0]
                
            elif input_type == "Dropdown":
                # Get dropdown options
                option_elements = element.find_all('option')
                options = [opt.text.strip() for opt in option_elements 
                          if opt.text.strip() and opt.text.strip() != "Select an option"]
                
                # Check for selected option
                selected_option = element.find('option', selected=True)
                if selected_option and selected_option.text.strip() != "Select an option":
                    current_answer = selected_option.text.strip()
                    
            elif input_type in ["Text Input", "Email Input", "Phone Input"]:
                # Check for existing input value
                input_element = element.find('input')
                if input_element and input_element.get('value'):
                    current_answer = input_element.get('value')
            
            question_count += 1
            questions.append({
                'number': question_count,
                'question': question_text,
                'type': input_type,
                'required': required,
                'options': options if options else None,
                'currentAnswer': current_answer
            })
    
    # After collecting questions, save them to JSON
    saveQuestionsToJson(questions)
    
    # Continue with printing summary
    print(f"\nFound {question_count} questions in the form:")
    for q in questions:
        required_text = "(Required)" if q['required'] else "(Optional)"
        print(f"{q['number']}. {q['question']}")
        print(f"   Type: {q['type']} {required_text}")
        if q['options']:
            print(f"   Options: {', '.join(q['options'])}")
        print()

def saveQuestionsToJson(new_questions):
    """
    Save questions to a JSON file, avoiding duplicates
    """
    json_file = 'linkedin_questions.json'
    existing_questions = {}
    
    # Load existing questions if file exists
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                existing_questions = json.load(f)
        except json.JSONDecodeError:
            print("Error reading existing JSON file. Creating new file.")
    
    # Process each new question
    for question in new_questions:
        # Create a unique key based on question text and type
        question_key = f"{question['question']}_{question['type']}"
        
        # Only add if question doesn't exist or update if it has different options
        if question_key not in existing_questions:
            # Add additional metadata
            question_data = {
                'question': question['question'],
                'type': question['type'],
                'required': question['required'],
                'options': question['options'],
                'currentAnswer': question['currentAnswer'],
                'verified': False,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }
            existing_questions[question_key] = question_data
        else:
            # Update last seen time, options, and current answer if they've changed
            existing_data = existing_questions[question_key]
            existing_data['last_seen'] = datetime.now().isoformat()
            
            # Update options if they've changed
            if existing_data['options'] != question['options']:
                existing_data['options'] = question['options']
                print(f"Updated options for question: {question['question']}")
            
            # Update current answer if it's different and not None
            if question['currentAnswer'] is not None:
                existing_data['currentAnswer'] = question['currentAnswer']
                print(f"Updated current answer for question: {question['question']}")
    
    # Save updated questions back to file
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(existing_questions, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved questions to {json_file}")
    except Exception as e:
        print(f"Error saving questions to JSON: {str(e)}")

    # TODO: Add parsing logic here to extract:
    # - Input fields
    # - Required fields
    # - Dropdown options
    # - etc. 
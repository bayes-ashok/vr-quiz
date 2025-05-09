import io
import json
from collections import Counter
from django.shortcuts import get_object_or_404, render
from .models import KeyValueData, SurveyResponse
import requests
from django.db import models  # Import models for aggregation

import requests


def index(request):
    # API endpoints
    urls = [
        "https://services.api.unity.com/cloud-save/v1/data/projects/77f104be-1501-4cb5-b939-e690de43ec34/environments/002f4514-3bea-412a-a9dc-37e1ba68de0f/players/GmgJzvzMCAEFHw5IfkAGyHVchtvr/items",
    ]
    
    auth_header = "Basic MDgwMTMzNzktMzdlMy00YzE1LTk4ZjQtYjVjZWE2MmU4NmVhOlJBVUxUWFhwdHM2V3ZTR3ZCVVhVVW1zMXNkb2h2b3VP"

    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json"
    }

    # Correct answers for rest questions
    correct_answers = [[2], [1], [2], [2], [2], [1], [2], [1], [1], [1], [1], [1], [2], [2], [1], [1], [1], [2], [1], [1], [0], [1], [0], [0, 2, 1], [1], [1], [2]]

    key_value_pairs = {}  # For passing to the template

    def compare_answers(user_answer, correct_answer):
        if len(user_answer) == 1 and len(correct_answer) == 1:
            return user_answer == correct_answer
        else:
            user_set = set(user_answer)
            correct_set = set(correct_answer)
            valid_numbers = {0, 1, 2}
            return user_set == correct_set and all(x in valid_numbers for x in user_set)

    try:
        for url in urls:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            for item in data.get('results', []):
                key = item.get('key')
                answers = item.get('value', {}).get('answers', [])
                score = item.get('value', {}).get('score', 0)

                first_five = answers[:5] if len(answers) >= 5 else answers
                rest_questions = answers[5:] if len(answers) > 5 else []

                correctness = []
                for user_answer, correct_answer in zip(rest_questions, correct_answers):
                    if compare_answers(user_answer, correct_answer):
                        correctness.append(1)
                    else:
                        correctness.append(0)

                correct_sum = sum(correctness)
                skipped = correct_sum != score

                first_five_str = json.dumps(first_five)
                rest_questions_str = json.dumps(rest_questions)
                correctness_str = ','.join(map(str, correctness))

                # Update or create the model instance, preserving existing name and gender
                SurveyResponse.objects.update_or_create(
                    id=key,
                    defaults={
                        'selected_options_from_one_to_five': first_five_str,
                        'selected_options_rest_questions': rest_questions_str,
                        'score': score,
                        'correctly_answered': correctness_str,
                        'skipped': skipped,
                    }
                )

        # Fetch all survey responses from the model
        responses = SurveyResponse.objects.all()
        for response in responses:
            gender_display = response.get_gender_display() if response.gender else ''
            key_value_pairs[response.id] = {
                'name': response.name or '',
                'gender': gender_display,
                'score': response.score,
                'skipped': 'Yes' if response.skipped else 'No',
                'correctly_answered': response.correctly_answered or ''
            }

    except requests.exceptions.RequestException as e:
        print("Error:", e)

    return render(request, 'index.html', {'key_value_pairs': key_value_pairs})

import matplotlib.pyplot as plt
from django.shortcuts import render
from io import BytesIO
import base64
def analytics(request):
    # Initialize data structures
    survey_data = {
        'q1': Counter(), 'q2': Counter(), 'q3': Counter(), 'q4': Counter(), 'q5': Counter()
    }
    quiz_data = {f'q{i}': Counter() for i in range(6, 33)}
    correctness_data = {f'q{i}': {'correct': 0, 'total': 0} for i in range(6, 33)}
    skipped_correctness = {f'q{i}': {'skipped': {'correct': 0, 'total': 0}, 'not_skipped': {'correct': 0, 'total': 0}} for i in range(6, 33)}
    skipped_distribution = {'skipped': 0, 'not_skipped': 0}

    # Option mappings for survey questions
    survey_options = {
        'q1': {0: 'Very light', 1: 'Manageable', 2: 'Heavy', 3: 'Very heavy'},
        'q2': {0: 'Strongly agree', 1: 'Agree', 2: 'Neutral', 3: 'Disagree', 4: 'Strongly disagree'},
        'q3': {0: 'Excellent', 1: 'Good', 2: 'Average', 3: 'Poor', 4: 'Very poor'},
        'q4': {0: 'Always', 1: 'Often', 2: 'Sometimes', 3: 'Rarely', 4: 'Never'},
        'q5': {0: 'Inspiring students', 1: 'Professional recognition', 2: 'Opportunities for growth', 3: 'Salary and benefits', 4: 'Academic freedom'}
    }

    # Option mappings for quiz questions (simplified, using indices for brevity)
    quiz_options = {f'q{i}': {j: chr(65 + j) for j in range(5)} for i in range(6, 33)}  # A, B, C, D, E
    quiz_options['q29'] = {0: 'Mosaic plagiarism', 1: 'Code plagiarism', 2: 'Self-plagiarism', 3: 'Fabricated plagiarism'}

    responses = SurveyResponse.objects.all()
    total_responses = responses.count()

    for response in responses:
        try:
            # Parse survey answers
            survey_answers = json.loads(response.selected_options_from_one_to_five or '[]')
            for i, answer in enumerate(survey_answers[:5], 1):
                if answer:
                    if i == 5:  # Multi-select for Q5
                        for opt in answer:
                            survey_data[f'q{i}'][opt] += 1
                    else:
                        survey_data[f'q{i}'][answer[0]] += 1

            # Parse quiz answers and correctness
            quiz_answers = json.loads(response.selected_options_rest_questions or '[]')
            correctness = [int(x) for x in (response.correctly_answered or '').split(',') if x]
            for i, (answer, correct) in enumerate(zip(quiz_answers, correctness), 6):
                if answer:
                    if i == 29:  # Multi-select for Q29
                        for opt in answer:
                            quiz_data[f'q{i}'][opt] += 1
                    else:
                        quiz_data[f'q{i}'][answer[0]] += 1
                    correctness_data[f'q{i}']['total'] += 1
                    correctness_data[f'q{i}']['correct'] += correct
                    # Track skipped vs. non-skipped correctness
                    skip_key = 'skipped' if response.skipped else 'not_skipped'
                    skipped_correctness[f'q{i}'][skip_key]['total'] += 1
                    skipped_correctness[f'q{i}'][skip_key]['correct'] += correct

            # Track skipped distribution
            skipped_distribution['skipped' if response.skipped else 'not_skipped'] += 1

        except json.JSONDecodeError:
            continue

    # Prepare chart data
    survey_chart_data = {}
    for q, counter in survey_data.items():
        labels = [survey_options[q].get(k, str(k)) for k in sorted(counter.keys())]
        values = [counter.get(k, 0) / max(total_responses, 1) * 100 for k in sorted(counter.keys())]
        chart_type = 'pie' if q == 'q5' else 'bar'
        scales = {} if chart_type == 'pie' else {'y': {'beginAtZero': True, 'title': {'display': True, 'text': 'Percentage (%)'}}}
        legend_display = chart_type == 'pie'
        survey_chart_data[q] = {
            'labels': labels,
            'values': values,
            'type': chart_type,
            'scales': json.dumps(scales),  # Convert to JSON string for safe template rendering
            'legend_display': legend_display
        }

    quiz_chart_data = {}
    for q, counter in quiz_data.items():
        labels = [quiz_options[q].get(k, str(k)) for k in sorted(counter.keys())]
        values = [counter.get(k, 0) / max(total_responses, 1) * 100 for k in sorted(counter.keys())]
        quiz_chart_data[q] = {'labels': labels, 'values': values}

    correctness_chart_data = {
        'labels': [f'Q{i}' for i in range(6, 33)],
        'values': [
            (data['correct'] / max(data['total'], 1) * 100) if data['total'] > 0 else 0
            for data in correctness_data.values()
        ]
    }

    skipped_correctness_chart_data = {
        'labels': [f'Q{i}' for i in range(6, 33)],
        'skipped': [
            (data['skipped']['correct'] / max(data['skipped']['total'], 1) * 100) if data['skipped']['total'] > 0 else 0
            for data in skipped_correctness.values()
        ],
        'not_skipped': [
            (data['not_skipped']['correct'] / max(data['not_skipped']['total'], 1) * 100) if data['not_skipped']['total'] > 0 else 0
            for data in skipped_correctness.values()
        ]
    }

    skipped_pie_data = {
        'labels': ['Skipped', 'Not Skipped'],
        'values': [
            skipped_distribution['skipped'] / max(total_responses, 1) * 100,
            skipped_distribution['not_skipped'] / max(total_responses, 1) * 100
        ]
    }

    context = {
        'survey_chart_data': survey_chart_data,
        'quiz_chart_data': quiz_chart_data,
        'correctness_chart_data': correctness_chart_data,
        'skipped_correctness_chart_data': skipped_correctness_chart_data,
        'skipped_pie_data': skipped_pie_data,
        'total_responses': total_responses
    }

    return render(request, 'analytics.html', context)


def generate_chart(data):
    correct = data.count(1)
    incorrect = data.count(0)
    indices = list(range(1, len(data) + 1))
    
    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Bar Chart
    axes[0].bar(['Correct', 'Incorrect'], [correct, incorrect], color=['green', 'red'])
    axes[0].set_title("Correct vs Incorrect")
    
    # Line Chart
    axes[1].plot(indices, data, marker='o', linestyle='-', color='blue')
    axes[1].set_title("Progression of Answers")
    axes[1].set_xlabel("Question Number")
    axes[1].set_ylabel("Correct (1) / Incorrect (0)")
    
    # Pie Chart
    axes[2].pie([correct, incorrect], labels=['Correct', 'Incorrect'], autopct='%1.1f%%', colors=['green', 'red'])
    axes[2].set_title("Percentage of Correct Answers")
    
    plt.tight_layout()
    
    # Save to a BytesIO buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return img_str
def vul(request):
    record = None
    error = None
    chart_data = {}
    quiz_responses = []

    # Search functionality
    key = request.GET.get('key')
    if key:
        try:
            record = SurveyResponse.objects.get(id=key)
        except SurveyResponse.DoesNotExist:
            error = "No employee found with this ID."

    if record:
        # Quiz options mapping
        quiz_options = {f'q{i}': {j: chr(65 + j) for j in range(5)} for i in range(6, 33)}  # A, B, C, D, E
        quiz_options['q29'] = {0: 'Mosaic plagiarism', 1: 'Code plagiarism', 2: 'Self-plagiarism', 3: 'Fabricated plagiarism'}

        # Parse quiz answers and correctness
        quiz_answers = json.loads(record.selected_options_rest_questions or '[]')
        correctness = [int(x) for x in (record.correctly_answered or '').split(',') if x]

        # Line chart data for correctness
        chart_data = {
            'labels': [f'Q{i}' for i in range(6, 33)],
            'values': [100 if correct else 0 for correct in correctness]
        }

        # Quiz responses for table
        for i, (answer, correct) in enumerate(zip(quiz_answers, correctness), 6):
            q = f'q{i}'
            if answer:
                if i == 29:  # Multi-select for Q29
                    response_text = ', '.join(quiz_options[q].get(opt, str(opt)) for opt in answer)
                else:
                    response_text = quiz_options[q].get(answer[0], str(answer[0]))
                quiz_responses.append({
                    'question': f'Question {i}',
                    'response': response_text,
                    'correct': 'Correct' if correct else 'Incorrect'
                })

    context = {
        'record': record,
        'error': error,
        'chart_data': chart_data,
        'quiz_responses': quiz_responses
    }
    return render(request, 'vulnerable.html', context)
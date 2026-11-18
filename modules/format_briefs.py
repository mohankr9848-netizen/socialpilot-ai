"""Deterministic, editable production briefs. No claims or statistics invented."""
FORMATS = ('Single image', 'Carousel', 'Infographic', 'Short video / Reel', 'Explainer video', 'Text post', 'Poll', 'Story', 'Document post', 'Product demo')

def choose_format(index, platform, allowed=None):
    allowed = tuple(allowed or FORMATS)
    if not allowed:
        raise ValueError('Select at least one content format.')
    # Formats are user-selectable; rotate all choices instead of defaulting to images.
    return allowed[index % len(allowed)]


def make_brief(fmt, title, topic, audience, product='', source_url=''):
    base = {'format': fmt, 'audience': audience, 'product': product, 'source_url': source_url,
            'core_message': topic, 'editorial_note': 'Verify all product capabilities and claims against the linked source before publishing.'}
    if fmt == 'Carousel':
        base['slides'] = [
            {'slide': 1, 'headline': title, 'visual': 'Topic-specific opening illustration'},
            {'slide': 2, 'headline': 'The challenge', 'visual': f'Show the audience problem connected to {topic}'},
            {'slide': 3, 'headline': 'How it works', 'visual': 'Explain the process using a simple flow'},
            {'slide': 4, 'headline': 'What to evaluate', 'visual': 'Three practical evaluation criteria'},
            {'slide': 5, 'headline': 'Key takeaway', 'visual': 'One memorable summary and CTA'}]
    elif fmt == 'Infographic':
        base['infographic'] = {'title': title, 'sections': ['The operational challenge', 'Relevant workflow', 'Key considerations', 'Practical takeaway'], 'layout': 'Four-stage connected flow; no invented numbers'}
    elif fmt in ('Short video / Reel', 'Explainer video', 'Product demo'):
        duration = 30 if fmt == 'Short video / Reel' else 60
        base['video'] = {'duration_seconds': duration, 'aspect_ratio': '9:16' if fmt == 'Short video / Reel' else '16:9',
                         'scenes': [
                             {'seconds': f'0–{duration//4}', 'visual': f'Hook: introduce {topic}', 'voiceover': f'What should {audience} know about {topic}?'},
                             {'seconds': f'{duration//4}–{duration//2}', 'visual': 'Show the real-world problem; avoid unsupported claims', 'voiceover': 'Start by identifying the current workflow and its limitations.'},
                             {'seconds': f'{duration//2}–{3*duration//4}', 'visual': 'Illustrate the product or workflow using approved source details', 'voiceover': f'Explore where {topic} fits and which requirements matter most.'},
                             {'seconds': f'{3*duration//4}–{duration}', 'visual': 'Summary and branded CTA', 'voiceover': 'Review your requirements and explore the solution in more detail.'}]}
    elif fmt == 'Poll':
        base['poll'] = {'question': f'What is your biggest priority when evaluating {topic}?', 'options': ['Ease of integration', 'Operational visibility', 'Team efficiency', 'Scalability'], 'follow_up': 'Invite respondents to explain their choice.'}
    elif fmt == 'Story':
        base['story_frames'] = [{'frame': 1, 'overlay': title}, {'frame': 2, 'overlay': f'What makes {topic} challenging?'}, {'frame': 3, 'overlay': 'Explore the workflow and share your perspective'}]
    elif fmt == 'Document post':
        base['pages'] = [{'page': i+1, 'heading': h} for i,h in enumerate([title, 'Context and challenge', 'Process overview', 'Evaluation checklist', 'Key takeaway'])]
    elif fmt == 'Text post':
        base['text_outline'] = ['Attention-grabbing hook', 'Specific audience problem', 'Practical insight', 'One actionable takeaway', 'Discussion question']
    else:
        base['image'] = {'headline': title, 'visual_direction': f'Illustrate {topic} for {audience}', 'supporting_line': 'Use one concise benefit verified against source material'}
    return base

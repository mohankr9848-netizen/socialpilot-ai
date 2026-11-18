"""Presentation guidance for a connected, source-aware marketing workflow."""

def research_lineage(post):
    brief = post.get('content_brief') or {}
    return {'product': brief.get('product') or '', 'source_url': brief.get('source_url') or '', 'audience': brief.get('audience') or '', 'format': post.get('content_type') or ''}

def production_guidance(fmt):
    guidance = {
        'Single image': 'Create one branded graphic with a clear headline, illustration and CTA.',
        'Carousel': 'Use the slide-by-slide brief to design separate slide images; export each slide before posting.',
        'Infographic': 'Use the infographic structure to build a readable, evidence-backed diagram.',
        'Short video / Reel': 'Use the timed scenes and voiceovers as a storyboard; this tool does not render video.',
        'Explainer video': 'Produce a multi-scene storyboard and voiceover before assembling a video.',
        'Text post': 'Use the caption and text outline; a graphic is optional.',
        'Poll': 'Use the question and response options in the native social platform poll feature.',
        'Story': 'Create a separate frame for each story panel.',
        'Document post': 'Design each document page separately and assemble into a document.',
        'Product demo': 'Use the demo scenes and verified product details to plan a screen recording.'}
    return guidance.get(fmt, 'Review the source-backed production brief before publishing.')

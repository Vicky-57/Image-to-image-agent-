from flask import Flask, request, jsonify, send_file, session, render_template
from werkzeug.utils import secure_filename
import os
from google import genai
from google.genai import types
import uuid
from dotenv import load_dotenv
import shutil
import json

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max for multiple images
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create directories if they don't exist
os.makedirs('uploads/input', exist_ok=True)
os.makedirs('uploads/reference', exist_ok=True)
os.makedirs('generated', exist_ok=True)
os.makedirs('templates', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)

def get_user_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['tweaks_used'] = 0
        session.permanent = True
    return session['user_id']

def detect_image_views(gemini_files, file_type="input"):
    """
    Auto-detect views of images (top, side, front, etc.)
    Returns a list of view types corresponding to each file
    """
    if len(gemini_files) == 1:
        return ["single"]
    
    view_detection_prompt = f"""
    You are an expert in interior design and spatial analysis. Analyze these {file_type} images and identify the camera angle/view for each image.
    
    For each image, determine if it shows:
    - "top": Top-down/overhead view, bird's eye view
    - "front": Front-facing view, main perspective
    - "side": Side view, profile view
    - "corner": Corner/angled view showing multiple walls
    - "detail": Close-up detail view
    - "wide": Wide/panoramic view
    
    Respond with a JSON array where each element corresponds to an image (in order) with the view type.
    Example: ["front", "side", "top"]
    
    Only respond with the JSON array, no other text.
    """
    
    # Prepare content for view detection
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=view_detection_prompt)
            ] + [types.Part.from_uri(file_uri=f.uri, mime_type=f.mime_type) for f in gemini_files],
        )
    ]
    
    try:
        # Generate view detection
        config = types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for consistent classification
            top_p=0.8,
            max_output_tokens=1024,
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=config,
        )
        
        # Parse the response
        if response.candidates and response.candidates[0].content:
            response_text = response.candidates[0].content.parts[0].text.strip()
            # Clean up the response in case it has extra formatting
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            views = json.loads(response_text)
            
            # Validate we have the right number of views
            if len(views) == len(gemini_files):
                return views
        
    except Exception as e:
        print(f"View detection failed: {e}")
    
    # Fallback to sequential mapping
    fallback_views = ["front", "side", "top", "corner", "detail"]
    views = []
    for i in range(len(gemini_files)):
        view_type = fallback_views[i] if i < len(fallback_views) else f"view_{i+1}"
        views.append(view_type)
    return views

def match_views_for_transformation(input_files, input_views, reference_files, reference_views):
    """
    Match input views with reference views for consistent transformation
    Returns list of (input_file, reference_file, view_type) tuples
    """
    matched_pairs = []
    
    # Create mappings for easier lookup
    input_view_map = {view: file for view, file in zip(input_views, input_files)}
    reference_view_map = {view: file for view, file in zip(reference_views, reference_files)}
    
    # First, try direct view matching
    matched_input_views = set()
    matched_reference_views = set()
    
    for input_view in input_views:
        if input_view in reference_view_map and input_view not in matched_input_views:
            matched_pairs.append((
                input_view_map[input_view], 
                reference_view_map[input_view], 
                input_view
            ))
            matched_input_views.add(input_view)
            matched_reference_views.add(input_view)
    
    # Handle remaining unmatched inputs
    remaining_input_views = [v for v in input_views if v not in matched_input_views]
    remaining_reference_views = [v for v in reference_views if v not in matched_reference_views]
    remaining_reference_files = [reference_view_map[v] for v in remaining_reference_views]
    
    # Pair remaining inputs with remaining references
    for i, input_view in enumerate(remaining_input_views):
        if i < len(remaining_reference_files):
            ref_view = remaining_reference_views[i]
            matched_pairs.append((
                input_view_map[input_view],
                remaining_reference_files[i],
                f"{input_view}_to_{ref_view}"
            ))
    
    return matched_pairs

def get_style_description(style):
    """Architecture-focused style descriptions"""
    descriptions = {
        'modern': 'clean geometric lines, minimal ornamentation, open floor plans, large windows, neutral color palettes, smooth surfaces',
        'rustic': 'natural wood beams, stone textures, warm earth tones, handcrafted elements, traditional joinery, cozy proportions',
        'industrial': 'exposed structural elements, raw materials, metal fixtures, concrete surfaces, high ceilings, utilitarian aesthetics',
        'scandinavian': 'light wood finishes, white walls, functional design, natural lighting, simple forms, hygge comfort',
        'traditional': 'classical proportions, rich wood millwork, detailed moldings, established color schemes, formal arrangements',
        'contemporary': 'current design trends, mixed materials, bold architectural features, flexible living spaces',
        'minimalist': 'essential elements only, clean surfaces, abundant natural light, functional built-ins, neutral materials',
        'bohemian': 'eclectic mix of textures, rich color layers, artistic elements, global influences, relaxed arrangements',
        'mediterranean': 'warm stucco walls, natural stone, arched openings, terra cotta elements, outdoor integration',
        'farmhouse': 'shiplap walls, barn-style elements, vintage fixtures, natural materials, comfortable functionality'
    }
    return descriptions.get(style, '')

def get_finish_description(finish):
    """Architecture-focused finish descriptions with material properties"""
    descriptions = {
        'matte': 'non-reflective surfaces, subtle texture variation, reduced glare, sophisticated understated appearance',
        'glossy': 'high-shine surfaces, strong light reflection, smooth polished textures, formal elegant appearance',  
        'textured': 'varied surface relief, tactile material quality, visual depth and interest, natural material feel',
        'satin': 'subtle semi-gloss sheen, balanced light reflection, elegant sophisticated finish, versatile application',
        'distressed': 'weathered patina, vintage character marks, aged material appearance, rustic authenticity',
        'polished': 'mirror-like surfaces, maximum light reflection, premium luxury appearance, high-end materials'
    }
    return descriptions.get(finish, '')

def get_theme_description(theme):
    """Enhanced theme descriptions with more room types"""
    descriptions = {
        'kitchen': 'kitchen space with cabinets, countertops, cooking areas, and dining elements',
        'bathroom': 'bathroom space with fixtures, tiles, bathing areas, and storage',
        'living': 'living room with seating, entertainment areas, and social spaces',
        'bedroom': 'bedroom with sleeping area, storage, and personal retreat elements',
        'dining': 'dining room with table, seating, and entertaining features',
        'office': 'home office with workspace, storage, and productivity elements',
        'entryway': 'entryway or foyer with welcoming elements and storage solutions',
        'laundry': 'laundry room with washing facilities, storage, and utility elements',
        'storage': 'storage room with organizational systems and utility features',
        'basement': 'basement space with recreational or utility purposes',
        'attic': 'attic space with sloped ceilings and unique architectural elements',
        'garage': 'garage space with storage, workspace, and utility functions',
        'closet': 'walk-in closet with clothing storage and dressing area'
    }
    return descriptions.get(theme, 'interior space')

def create_multi_view_consistency_prompt(view_type, all_view_types, style, finish, theme, context):
    """Create an architecture-focused consistency prompt for multi-view transformations"""
    
    # Handle None selections
    style_text = ""
    if style and style.strip():
        style_text = f"- Style Preference: {style.title()} - {get_style_description(style)}\n"
    
    finish_text = ""
    if finish and finish.strip():
        finish_text = f"- Surface Finish: {finish.title()} - {get_finish_description(finish)}\n"
    
    theme_text = ""
    if theme and theme.strip():
        theme_text = f"- Space Type: {theme.title()} - {get_theme_description(theme)}\n"
    else:
        theme_text = "- Space Type: Analyze and optimize for detected room function\n"
    
    return f"""
    You are a PROFESSIONAL ARCHITECTURAL RENDERER creating CONNECTED MULTI-VIEW TRANSFORMATIONS.
    
    🏗️ ARCHITECTURAL CONSISTENCY REQUIREMENTS (ABSOLUTELY CRITICAL):
    - This is the {view_type} view of a CONNECTED architectural space with views: {', '.join(all_view_types)}
    - PRESERVE exact spatial proportions and architectural layout from input
    - ENSURE structural elements connect logically across all views
    - MAINTAIN consistent material properties, lighting, and atmospheric conditions
    - CREATE photorealistic renderings with proper depth, shadows, and reflections
    
    🎯 MULTI-VIEW SPATIAL LOGIC:
    - ALL VIEWS must represent the SAME PHYSICAL SPACE from different angles
    - Architectural elements must align: if there's a window in front view, it should appear in side view
    - Materials, colors, and finishes must be IDENTICAL across all connected views
    - Lighting sources and shadows must be consistent with the space's actual configuration
    - Design elements must flow naturally between different camera angles
    
    🎨 DESIGN TRANSFORMATION SPECIFICATIONS:
    {style_text}{finish_text}{theme_text}- Current View Angle: {view_type}
    
    🔧 PROFESSIONAL RENDERING INSTRUCTIONS:
    1. Maintain the exact architectural structure and proportions of the input {view_type} view
    2. Extract complete design aesthetic from the corresponding reference view
    3. Apply consistent materials, lighting, and styling across this connected space
    4. Ensure this view harmonizes perfectly with other angles of the same room
    5. Create professional-grade architectural rendering quality
    6. Optimize architectural details (windows, doors, ceiling) only if they enhance the design
    {"7. Integrate specified style preferences while maintaining spatial consistency" if style or finish else "7. Draw primary inspiration from reference aesthetic while preserving input architecture"}
    
    ⚠️ ARCHITECTURAL VALIDATION CHECKLIST:
    - Would these connected views represent the same buildable space?
    - Are materials and finishes identical to other views?
    - Does the lighting logically connect with other camera angles?
    - Are proportions and perspectives architecturally accurate?
    - Do structural elements align across different views?
    
    CONTEXT: {context if context else 'Create a professional architectural rendering that maintains perfect spatial consistency across all connected views while achieving complete aesthetic transformation.'}
    
    Generate a photorealistic {view_type} view that represents part of a cohesively designed architectural space with professional rendering quality.
    """

@app.route('/generate', methods=['POST'])
def generate_interior():
    user_id = get_user_session()
    
    # Get form data - handle empty strings as None
    context = request.form.get('context', '').strip()
    selected_style = request.form.get('style', '').strip() or None
    selected_finish = request.form.get('finish', '').strip() or None
    selected_theme = request.form.get('theme', '').strip() or None
    
    # Get uploaded files
    input_files = request.files.getlist('input_images')
    reference_files = request.files.getlist('reference_images')
    
    # Validate files
    if not input_files or not reference_files:
        return jsonify({'error': 'Both input and reference images are required'}), 400
    
    # Filter out empty files
    input_files = [f for f in input_files if f.filename != '']
    reference_files = [f for f in reference_files if f.filename != '']
    
    if not input_files or not reference_files:
        return jsonify({'error': 'Please select valid image files'}), 400
    
    # Check file extensions
    for file in input_files + reference_files:
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PNG, JPG, JPEG files allowed'}), 400
    
    try:
        # Save input images
        saved_input_files = []
        input_gemini_files = []
        
        for i, input_file in enumerate(input_files):
            input_filename = f"uploads/input/{user_id}_input_{i}_{uuid.uuid4().hex[:8]}.jpg"
            input_file.save(input_filename)
            saved_input_files.append(input_filename)
            
            # Upload to Gemini
            input_gemini_file = client.files.upload(file=input_filename)
            input_gemini_files.append(input_gemini_file)
        
        # Save reference images
        saved_reference_files = []
        reference_gemini_files = []
        
        for i, reference_file in enumerate(reference_files):
            reference_filename = f"uploads/reference/{user_id}_reference_{i}_{uuid.uuid4().hex[:8]}.jpg"
            reference_file.save(reference_filename)
            saved_reference_files.append(reference_filename)
            
            # Upload to Gemini
            reference_gemini_file = client.files.upload(file=reference_filename)
            reference_gemini_files.append(reference_gemini_file)
        
        # Detect views for both input and reference images
        print("Detecting input image views...")
        input_views = detect_image_views(input_gemini_files, "input")
        print(f"Input views detected: {input_views}")
        
        print("Detecting reference image views...")
        reference_views = detect_image_views(reference_gemini_files, "reference")
        print(f"Reference views detected: {reference_views}")
        
        # Determine if this is multi-view transformation
        is_multi_view = len(input_files) > 1 and len(reference_files) > 1
        
        if is_multi_view:
            print("Multi-view transformation detected")
            # Multi-view transformation with spatial consistency
            matched_pairs = match_views_for_transformation(
                input_gemini_files, input_views, 
                reference_gemini_files, reference_views
            )
            print(f"Matched pairs: {[(pair[2]) for pair in matched_pairs]}")
        else:
            print("Single transformation mode")
            # Single transformation (original logic)
            if len(input_gemini_files) == 1:
                # One input, multiple references
                matched_pairs = [(input_gemini_files[0], ref_file, f"style_{i+1}") 
                               for i, ref_file in enumerate(reference_gemini_files)]
            else:
                # Multiple inputs, one reference
                matched_pairs = [(input_file, reference_gemini_files[0], f"input_{i+1}") 
                               for i, input_file in enumerate(input_gemini_files)]
        
        # Generate outputs
        generated_outputs = []
        all_view_types = [pair[2] for pair in matched_pairs] if is_multi_view else []
        
        for pair_idx, (input_file, reference_file, view_description) in enumerate(matched_pairs):
            output_filename = f"generated/{user_id}_output_{pair_idx}_{uuid.uuid4().hex[:8]}.jpg"
            
            if is_multi_view:
                # Use consistency-focused prompt for multi-view
                prompt = create_multi_view_consistency_prompt(
                    view_description, all_view_types, 
                    selected_style, selected_finish, selected_theme, context
                )
            else:
                # Enhanced single transformation prompt with None handling
                style_text = ""
                if selected_style:
                    style_text = f"- Style: {selected_style.title()} - {get_style_description(selected_style)}\n"
                
                finish_text = ""
                if selected_finish:
                    finish_text = f"- Finish: {selected_finish.title()} - {get_finish_description(selected_finish)}\n"
                
                theme_text = ""
                if selected_theme:
                    theme_text = f"- Theme: {selected_theme.title()} - {get_theme_description(selected_theme)}\n"
                else:
                    theme_text = "- Theme: Auto-detect room type from context\n"
                
# Replace the existing single transformation prompt with this enhanced version:
                prompt = f"""
                You are a PROFESSIONAL ARCHITECTURAL RENDERER specializing in realistic interior design transformations.

                🏗️ ARCHITECTURAL REQUIREMENTS (CRITICAL):
                - Maintain the EXACT room proportions and spatial layout from the input image
                - Preserve structural integrity and realistic architectural elements
                - Apply photorealistic lighting with proper shadows and reflections
                - Ensure materials have authentic textures, depth, and physical properties
                - Maintain proper perspective and spatial relationships

                🎨 DESIGN TRANSFORMATION REQUIREMENTS:
                - Extract and apply the COMPLETE design language from the reference image:
                * Color palettes and material choices
                * Furniture styles, arrangements, and scale
                * Lighting fixtures, window treatments, and accessories
                * Textures, patterns, and surface finishes
                * Atmospheric qualities and mood
                - You may modify window styles, ceiling treatments, and architectural details if they enhance the overall design
                - Furniture placement can be optimized for better flow and functionality
                - Maintain architectural logic (proper door/window proportions, realistic ceiling heights, etc.)

                🔧 TECHNICAL SPECIFICATIONS:
                {style_text}{finish_text}{theme_text}

                TRANSFORMATION INSTRUCTIONS:
                1. Analyze the spatial architecture and proportions of the input room
                2. Extract the complete aesthetic DNA from the reference image
                3. Seamlessly blend reference styling with input architecture
                4. Ensure every surface, material, and element looks professionally rendered
                5. Apply realistic lighting that enhances both form and function
                6. Create depth through proper shadows, reflections, and material properties
                {"7. Prioritize the specified design preferences while maintaining architectural integrity" if selected_style or selected_finish else "7. Let the reference image guide the complete aesthetic transformation"}

                ⚠️ QUALITY CHECKLIST:
                - Does this look like a professional architectural rendering?
                - Are proportions and perspectives architecturally sound?
                - Do materials look authentic with proper texture and depth?
                - Is the lighting realistic with appropriate shadows?
                - Would this design be buildable and functional in real life?

                Additional Requirements: {context if context else 'Create a professional architectural rendering that seamlessly blends the spatial qualities of the input with the complete design aesthetic of the reference image.'}

                Generate a photorealistic architectural rendering that maintains structural integrity while achieving complete aesthetic transformation.
                """
            
            # Prepare content
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(file_uri=input_file.uri, mime_type=input_file.mime_type),
                        types.Part.from_uri(file_uri=reference_file.uri, mime_type=reference_file.mime_type),
                        types.Part.from_text(text=prompt),
                    ],
                )
            ]
            
            # Generation config with adjusted parameters for consistency
            # Generation config with enhanced parameters for architectural accuracy
            config = types.GenerateContentConfig(
                temperature=0.4 if is_multi_view else 0.5,  # Lower temperature for more consistency
                top_p=0.75 if is_multi_view else 0.85,     # Reduced randomness for better quality
                max_output_tokens=8192,
                response_modalities=["image", "text"],
                response_mime_type="text/plain",
            )
            
            # Generate image
            print(f"Generating {view_description}...")
            image_generated = False
            for chunk in client.models.generate_content_stream(
                model="gemini-2.0-flash-exp-image-generation",
                contents=contents,
                config=config,
            ):
                if (chunk.candidates and chunk.candidates[0].content and 
                    chunk.candidates[0].content.parts and 
                    chunk.candidates[0].content.parts[0].inline_data):
                    
                    save_binary_file(output_filename, chunk.candidates[0].content.parts[0].inline_data.data)
                    generated_outputs.append({
                        'filename': output_filename,
                        'url': f'/view_image/{os.path.basename(output_filename)}',
                        'view_type': view_description,
                        'pair_index': pair_idx
                    })
                    image_generated = True
                    print(f"Generated {view_description} successfully")
                    break
            
            if not image_generated:
                return jsonify({'error': f'Failed to generate image for {view_description}'}), 500
        
        # Store session data
        session['current_images'] = [output['filename'] for output in generated_outputs]
        session['original_inputs'] = saved_input_files
        session['original_references'] = saved_reference_files
        session['tweaks_used'] = 0
        session['generation_params'] = {
            'style': selected_style,
            'finish': selected_finish,
            'theme': selected_theme,
            'context': context,
            'is_multi_view': is_multi_view
        }
        session['view_info'] = [{'view_type': output['view_type']} for output in generated_outputs]
        
        return jsonify({
            'success': True,
            'images': [{'url': output['url'], 'view_type': output['view_type']} for output in generated_outputs],
            'tweaks_remaining': 3 - session['tweaks_used'],
            'total_generated': len(generated_outputs),
            'generation_type': 'multi_view' if is_multi_view else 'single',
            'view_mapping': input_views if is_multi_view else None,
            'detected_views': {
                'input': input_views,
                'reference': reference_views
            }
        })
        
    except Exception as e:
        print(f"Error in generate_interior: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Clean up files on error
        for f in saved_input_files + saved_reference_files:
            if os.path.exists(f):
                os.remove(f)
        return jsonify({'error': str(e)}), 500

@app.route('/tweak', methods=['POST'])
def tweak_image():
    user_id = get_user_session()
    
    if session['tweaks_used'] >= 3:
        return jsonify({'error': 'You have used all your tweaks for this session'}), 400
    
    if 'current_images' not in session:
        return jsonify({'error': 'No images to tweak. Please generate images first.'}), 400
    
    data = request.json
    tweak_instruction = data.get('instruction', '')
    image_index = data.get('image_index', 0)
    
    if not tweak_instruction:
        return jsonify({'error': 'Tweak instruction is required'}), 400
    
    try:
        current_images = session['current_images']
        if image_index >= len(current_images):
            return jsonify({'error': 'Invalid image index'}), 400
        
        current_image_path = current_images[image_index]
        if not os.path.exists(current_image_path):
            return jsonify({'error': 'Original image not found'}), 400
        
        # Upload current image to Gemini
        current_gemini_file = client.files.upload(file=current_image_path)
        
        # Create tweak prompt
        params = session.get('generation_params', {})
        view_info = session.get('view_info', [{}])
        current_view = view_info[image_index].get('view_type', 'current view') if image_index < len(view_info) else 'current view'
        
        # Enhanced tweak prompt for multi-view consistency
        # Replace the existing tweak prompts with these enhanced versions:

        if params.get('is_multi_view', False):
            prompt = f"""
            🔧 PROFESSIONAL ARCHITECTURAL MODIFICATION - Multi-View Connected Space
            
            You are making precise modifications to the {current_view} of a CONNECTED architectural space with views: {', '.join(all_views)}
            
            ⚠️ CRITICAL ARCHITECTURAL CONSISTENCY:
            - This modification must maintain PERFECT consistency with other views of the same room
            - PRESERVE structural integrity and realistic material properties  
            - ENSURE changes look professionally executed with proper depth and texture
            - MAINTAIN consistent lighting, shadows, and atmospheric conditions
            - KEEP the same material choices and color accuracy across all views
            
            🎯 MODIFICATION REQUEST:
            {tweak_instruction}
            
            🔧 PROFESSIONAL EXECUTION REQUIREMENTS:
            ✅ Apply changes with architectural precision and realism
            ✅ Maintain photorealistic material properties and textures
            ✅ Ensure proper lighting and shadow integration
            ✅ Preserve the {params.get('style', 'current')} style consistency
            ✅ Keep {params.get('finish', 'current')} surface finish quality
            ✅ Stay true to the {params.get('theme', 'current')} space function
            ✅ Ensure changes integrate seamlessly with other room views
            ✅ Maintain professional architectural rendering standards
            ✅ Create realistic depth, not flat 2D-like modifications
            
            EXECUTE the modification with professional architectural precision while maintaining perfect consistency with other views of this connected space.
            """
        else:
            prompt = f"""
            🔧 PROFESSIONAL ARCHITECTURAL MODIFICATION
            
            You are a professional architectural renderer making precise modifications to this interior space.
            
            MODIFICATION REQUEST:
            {tweak_instruction}
            
            🏗️ ARCHITECTURAL EXECUTION STANDARDS:
            - Apply changes with realistic material properties and authentic textures
            - Ensure proper lighting integration with realistic shadows and reflections  
            - Maintain architectural logic and structural believability
            - Create three-dimensional depth, not flat surface changes
            - Preserve photorealistic rendering quality throughout
            - Ensure modifications look professionally executed and buildable
            
            DESIGN CONSISTENCY:
            - Maintain the overall {params.get('style', 'current')} design language
            - Preserve {params.get('finish', 'current')} surface finish quality  
            - Keep true to the {params.get('theme', 'current')} space functionality
            - Ensure changes enhance rather than compromise the design
            
            Execute this modification with professional precision, creating realistic three-dimensional changes that integrate seamlessly with the existing architecture and design.
            """
        
        # Prepare content for tweaking
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(file_uri=current_gemini_file.uri, mime_type=current_gemini_file.mime_type),
                    types.Part.from_text(text=prompt),
                ],
            )
        ]
        
        # Generation config
        # Generation config for tweaks
        config = types.GenerateContentConfig(
            temperature=0.3 if params.get('is_multi_view') else 0.4,  # Very low for precise modifications
            top_p=0.7 if params.get('is_multi_view') else 0.8,
            max_output_tokens=8192,
            response_modalities=["image", "text"],
            response_mime_type="text/plain",
        )
        
        # Generate tweaked image
        tweaked_filename = f"generated/{user_id}_tweaked_{image_index}_{uuid.uuid4().hex[:8]}.jpg"
        
        image_generated = False
        for chunk in client.models.generate_content_stream(
            model="gemini-2.0-flash-exp-image-generation",
            contents=contents,
            config=config,
        ):
            if (chunk.candidates and chunk.candidates[0].content and 
                chunk.candidates[0].content.parts and 
                chunk.candidates[0].content.parts[0].inline_data):
                
                save_binary_file(tweaked_filename, chunk.candidates[0].content.parts[0].inline_data.data)
                
                # Update session
                session['current_images'][image_index] = tweaked_filename
                session['tweaks_used'] += 1
                
                image_generated = True
                break
        
        if image_generated:
            return jsonify({
                'success': True,
                'image_url': f'/view_image/{os.path.basename(tweaked_filename)}',
                'tweaks_remaining': 3 - session['tweaks_used'],
                'image_index': image_index,
                'view_type': current_view
            })
        else:
            return jsonify({'error': 'No tweaked image generated'}), 500
        
    except Exception as e:
        print(f"Error in tweak_image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/view_image/<filename>')
def view_image(filename):
    return send_file(f'generated/{filename}')

@app.route('/download_image')
def download_image():
    image_index = request.args.get('index', 0, type=int)
    
    if 'current_images' not in session:
        return jsonify({'error': 'No images to download'}), 400
    
    current_images = session['current_images']
    if image_index >= len(current_images):
        return jsonify({'error': 'Invalid image index'}), 400
    
    current_image_path = current_images[image_index]
    if not os.path.exists(current_image_path):
        return jsonify({'error': 'Image file not found'}), 400
    
    # Get view info for filename
    view_info = session.get('view_info', [{}])
    view_type = view_info[image_index].get('view_type', f'view_{image_index + 1}') if image_index < len(view_info) else f'view_{image_index + 1}'
    
    return send_file(current_image_path, as_attachment=True, 
                    download_name=f'transformed_{view_type}_{image_index + 1}.jpg')

@app.route('/download_all')
def download_all():
    if 'current_images' not in session:
        return jsonify({'error': 'No images to download'}), 400
    
    import zipfile
    import tempfile
    
    current_images = session['current_images']
    view_info = session.get('view_info', [])
    
    # Create temporary zip file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
        for i, image_path in enumerate(current_images):
            if os.path.exists(image_path):
                view_type = view_info[i].get('view_type', f'view_{i + 1}') if i < len(view_info) else f'view_{i + 1}'
                zipf.write(image_path, f'transformed_{view_type}_{i + 1}.jpg')
    
    return send_file(temp_zip.name, as_attachment=True, 
                    download_name='transformed_interiors_multi_view.zip')

@app.route('/reset_session')
def reset_session():
    session.clear()
    return jsonify({'success': True, 'message': 'Session reset successfully'})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
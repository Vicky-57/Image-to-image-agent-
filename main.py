# from flask import Flask, request, jsonify, send_file, session, render_template
# from werkzeug.utils import secure_filename
# import os
# from google import genai
# from google.genai import types
# import uuid
# from dotenv import load_dotenv
# import shutil
# import json

# load_dotenv()

# app = Flask(__name__)
# app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max for multiple images
# app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# # Initialize Gemini client
# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# # Create directories if they don't exist
# os.makedirs('uploads/input', exist_ok=True)
# os.makedirs('uploads/reference', exist_ok=True)
# os.makedirs('generated', exist_ok=True)
# os.makedirs('templates', exist_ok=True)

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def save_binary_file(file_name, data):
#     with open(file_name, "wb") as f:
#         f.write(data)

# def get_user_session():
#     if 'user_id' not in session:
#         session['user_id'] = str(uuid.uuid4())
#         session['tweaks_used'] = 0
#         session.permanent = True
#     return session['user_id']


# def get_style_description(style):
#     """Enhanced architecture-focused style descriptions with photorealistic details"""
#     descriptions = {
#         'modern': 'ultra-clean geometric lines with precision edges, seamless minimal ornamentation, expansive open floor plans, floor-to-ceiling windows with visible glass reflections, sophisticated neutral color palettes with subtle tonal variations, polished smooth surfaces with realistic material sheen, contemporary designer furniture with accurate proportions',
#         'rustic': 'authentic natural wood beams with visible grain patterns and knots, genuine stone textures with depth and variation, warm earth tones with natural color gradients, handcrafted elements showing realistic craftsmanship details, traditional joinery with visible connections, cozy proportions with intimate scale, weathered finishes with natural patina',
#         'industrial': 'authentic exposed structural steel beams with realistic metal textures, raw concrete surfaces with visible aggregate and subtle imperfections, aged metal fixtures with oxidation and wear patterns, polished concrete floors with natural variations, dramatic high ceilings with proper perspective, utilitarian aesthetics with functional details, Edison bulbs with realistic filament glow',
#         'scandinavian': 'light blonde wood finishes with natural grain visible, pure white walls with soft light bounce, functional minimalist furniture with clean joinery, abundant diffused natural lighting through sheer curtains, simple geometric forms with precise edges, textured wool and linen fabrics, hygge comfort elements like sheepskin throws, subtle warm color accents',
#         'traditional': 'classical architectural proportions with proper molding details, rich mahogany or walnut wood with deep grain, detailed crown moldings with realistic shadow depth, established color schemes with layered tones, formal symmetrical arrangements, ornate hardware with metallic luster, plush upholstery with fabric texture detail',
#         'contemporary': 'current design trends with bold geometric forms, mixed materials showing distinct textures (wood, metal, glass, stone), dramatic architectural features with proper scale, flexible living spaces with multifunctional elements, statement lighting fixtures with realistic illumination, neutral base with strategic color pops, large format tiles or continuous flooring',
#         'minimalist': 'essential elements only with breathing room, pristine clean surfaces with subtle reflections, abundant natural light with soft shadows, functional built-ins with seamless integration, neutral materials (concrete, white oak, matte black steel), hidden storage solutions, monochromatic color schemes, emphasis on negative space and proportion',
#         'bohemian': 'eclectic layered textiles with varied patterns and textures, rich jewel-toned color palette, globally-inspired decorative elements, mixed wood furniture with different finishes, abundant plants with realistic foliage, vintage Persian or kilim rugs with intricate patterns, macramé and woven elements, collected artifacts with authentic detail',
#         'mediterranean': 'warm ochre and terracotta stucco walls with textured finish, natural limestone or travertine stone with visible variation, graceful arched openings with proper structural detail, wrought iron fixtures with authentic metalwork, terra cotta tile roofing or flooring, white-washed wood beams, seamless indoor-outdoor flow, cobalt blue accent tiles',
#         'farmhouse': 'shiplap or beadboard walls with visible wood grain and gaps, vintage barn-style sliding doors on black metal hardware, apron-front farmhouse sinks, distressed wood furniture with authentic wear patterns, subway tiles with classic layout, butcher block countertops with natural wood texture, vintage-style pendant lights, comfortable slipcovered furniture, open shelving with rustic brackets'
#     }
#     return descriptions.get(style, '')

# def get_finish_description(finish):
#     """Enhanced finish descriptions with precise material rendering properties"""
#     descriptions = {
#         'matte': 'completely non-reflective surfaces with no specular highlights, subtle micro-texture variation visible up close, reduced glare maintaining true material colors, sophisticated understated appearance with depth from texture rather than shine, light absorption creating soft edges, fingerprint-resistant quality implied by surface treatment',
#         'glossy': 'mirror-like high-shine surfaces with sharp specular reflections, strong directional light reflection showing environment, ultra-smooth polished texture with glass-like quality, formal elegant appearance with depth from reflections, crisp light catchlights, reflections of surrounding objects and lighting visible, wet-look finish on surfaces',
#         'textured': 'pronounced surface relief with visible shadow patterns, three-dimensional tactile material quality, visual depth from varied surface angles catching light differently, natural material feel with organic irregularity, shadows within texture creating complexity, rough or embossed patterns clearly visible, authentic material grain or weave',
#         'satin': 'subtle semi-gloss sheen with soft diffused reflections, balanced light reflection between matte and gloss, elegant sophisticated finish with gentle luminosity, versatile appearance working in multiple lighting conditions, pearl-like luster with directional highlight, smooth but not mirror-like surface quality',
#         'distressed': 'authentic weathered patina with natural aging patterns, vintage character marks showing realistic wear, aged material appearance with color variation and fading, deliberate distressing looking naturally evolved, exposed base materials through worn top layers, rustic authenticity with historical narrative, intentional imperfections in finish',
#         'polished': 'pristine mirror-like surfaces with crystal-clear reflections, maximum light reflection creating dramatic highlights, premium luxury appearance with flawless finish, high-end materials like polished marble or lacquer, sharp environmental reflections, wet-look depth, buffed to perfection with no visible imperfections'
#     }
#     return descriptions.get(finish, '')

# def get_theme_description(theme):
#     """Enhanced theme descriptions with photorealistic spatial details"""
#     descriptions = {
#         'kitchen': 'professional kitchen space with realistic cabinetry showing wood grain or paint finish, authentic countertop materials (granite, quartz, marble) with natural veining, functional cooking areas with proper appliance integration, task lighting with realistic shadows, backsplash with dimensional tiles, hardware with metallic finish, proper spatial clearances',
#         'bathroom': 'spa-like bathroom with authentic tile work showing grout lines, realistic plumbing fixtures with chrome or brass finish, natural stone or porcelain surfaces with proper texture, layered lighting (ambient, task, accent), glass shower enclosures with subtle reflections, textured towels and bath linens, steam and moisture implied by material choices',
#         'living': 'inviting living room with comfortable upholstered furniture showing fabric texture, layered lighting creating ambient glow, entertainment center integration, area rugs with visible pile and pattern, coffee table styling with realistic objects, window treatments with natural drape, architectural details like moldings or built-ins, proper furniture scale and spacing',
#         'bedroom': 'serene bedroom with luxurious bedding showing fabric folds and texture, bedside lighting with warm glow, dresser or storage furniture with realistic wood or finish, window treatments filtering natural light, area rug grounding the bed, decorative pillows with varied textures, nightstands with styled accessories, intimate scale and proportion',
#         'dining': 'elegant dining room with substantial dining table showing wood grain or finish, coordinated seating with upholstery detail, statement chandelier or pendant lighting with realistic illumination, buffet or sideboard with decorative styling, table setting with dishes and glassware, window treatments, area rug defining the space, proper clearances around furniture',
#         'office': 'productive home office with functional desk showing work surface material, ergonomic task seating, organized storage solutions (shelving, filing), task lighting with focused illumination, technology integration, inspirational artwork or vision board, window providing natural light, professional but personal styling',
#         'entryway': 'welcoming foyer with durable flooring material, console table or bench with realistic finish, mirror with decorative frame, coat storage solutions, table lamp or pendant lighting, area rug, decorative bowl or tray, artwork creating first impression, proper scale for traffic flow',
#         'laundry': 'efficient laundry room with front-load washer/dryer showing realistic appliance details, utility sink, organized storage cabinets, countertop for folding with proper surface material, task lighting, drying rack or hanging rod, tile or luxury vinyl flooring, functional hardware',
#         'storage': 'organized storage room with custom shelving systems, bins and baskets with realistic materials, labeled organization, proper lighting to see contents, durable flooring, potentially climate control elements, efficient use of vertical space',
#         'basement': 'finished basement space with proper ceiling treatment (drywall or exposed painted joists), appropriate flooring (carpet, LVP, stained concrete), defined zones (entertainment, workout, storage), adequate artificial lighting, furniture scaled for ceiling height, cozy atmosphere despite below-grade location',
#         'attic': 'converted attic space with exposed roof lines and proper insulation treatment, skylights or dormers providing natural light, creative furniture placement accommodating sloped ceilings, appropriate flooring, ambient lighting adapted to unique geometry, cozy built-ins maximizing awkward spaces',
#         'garage': 'organized garage with epoxy-coated or sealed concrete floor, wall-mounted storage systems, proper lighting (overhead fluorescent or LED), workbench area, tool organization, overhead storage racks, clean and functional appearance, automotive or workshop equipment',
#         'closet': 'luxurious walk-in closet with custom built-in cabinetry in light wood or white finish, organized clothing displays, island with drawers showing realistic hardware, full-length mirror, boutique-style lighting, seating area, shoe display shelving, accessory organization, carpet or luxury flooring'
#     }
#     return descriptions.get(theme, 'interior space')


# @app.route('/generate', methods=['POST'])
# def generate_interior():
#     user_id = get_user_session()
    
#     # Get form data
#     context = request.form.get('context', '').strip()
#     selected_style = request.form.get('style', '').strip() or None
#     selected_finish = request.form.get('finish', '').strip() or None
#     selected_theme = request.form.get('theme', '').strip() or None
#     preserve_layout = request.form.get('preserve_layout', 'true') == 'true'
#     enhance_realism = request.form.get('enhance_realism', 'true') == 'true'
    
#     # Get uploaded files
#     input_files = request.files.getlist('input_images')
#     reference_files = request.files.getlist('reference_images')
    
#     # Validation
#     if len(input_files) != 1 or len(reference_files) != 1:
#         return jsonify({'error': 'Please upload exactly 1 input image and 1 reference image'}), 400
    
#     input_file = input_files[0]
#     reference_file = reference_files[0]
    
#     if not allowed_file(input_file.filename) or not allowed_file(reference_file.filename):
#         return jsonify({'error': 'Only PNG, JPG, JPEG files allowed'}), 400
    
#     try:
#         # Save and upload files
#         input_filename = f"uploads/input/{user_id}_input_{uuid.uuid4().hex[:8]}.jpg"
#         reference_filename = f"uploads/reference/{user_id}_reference_{uuid.uuid4().hex[:8]}.jpg"
        
#         input_file.save(input_filename)
#         reference_file.save(reference_filename)
        
#         input_gemini_file = client.files.upload(file=input_filename)
#         reference_gemini_file = client.files.upload(file=reference_filename)
        
#         # Generate 3 variations
#         generated_outputs = []
        
#         for variation in range(3):
#             output_filename = f"generated/{user_id}_output_{variation}_{uuid.uuid4().hex[:8]}.jpg"
            
#             # Build ENHANCED photorealistic prompt
#             style_text = f"- **Style Requirements**: {selected_style.title()} - {get_style_description(selected_style)}\n" if selected_style else ""
#             finish_text = f"- **Surface Finish**: {selected_finish.title()} - {get_finish_description(selected_finish)}\n" if selected_finish else ""
#             theme_text = f"- **Space Type**: {selected_theme.title()} - {get_theme_description(selected_theme)}\n" if selected_theme else "- **Space Type**: Identify and render room type with authentic details\n"
            
#             layout_instruction = "CRITICAL: Maintain EXACT room dimensions, wall positions, window locations, and ceiling height from input image" if preserve_layout else "You may adjust room proportions for improved design while maintaining realistic architecture"
            
#             # ENHANCED REALISM SECTION
#             if enhance_realism:
#                 realism_instruction = """
#                 PHOTOREALISTIC RENDERING REQUIREMENTS (CRITICAL):
                
#                 LIGHTING SIMULATION (HIGHEST PRIORITY):
#                 - Simulate authentic THREE-POINT LIGHTING with key, fill, and rim lights
#                 - Create realistic SOFT SHADOWS with proper penumbra (soft edges)
#                 - Add AMBIENT OCCLUSION in corners and where objects meet surfaces
#                 - Include SPECULAR HIGHLIGHTS on reflective materials (glass, metal, polished wood)
#                 - Show LIGHT BOUNCE and color bleeding from surfaces
#                 - Render CAUSTICS (light patterns through glass/water)
#                 - Add subtle LENS FLARE or BLOOM on bright light sources
#                 - Create DEPTH through atmospheric perspective and light falloff
                
#                 MATERIAL AUTHENTICITY:
#                 - Wood: Show realistic grain patterns, knots, color variation, subtle sheen on finish
#                 - Metal: Render accurate reflections, anisotropic highlights, oxidation/patina where appropriate
#                 - Fabric: Display weave patterns, wrinkles, light absorption, subtle fuzz on edges
#                 - Glass: Show transparency with distortion, edge highlights, subtle reflections
#                 - Stone/Tile: Render natural variation in color/pattern, grout lines, subtle surface texture
#                 - Paint: Show slight texture, sheen variation, subtle color shifts in different lighting
                
#                 SURFACE QUALITY:
#                 - Add MICRO-DETAILS: dust particles in light rays, subtle surface imperfections
#                 - Include NORMAL MAPPING effects for texture depth without geometry
#                 - Show realistic WEAR PATTERNS on high-traffic areas
#                 - Add SUBSURFACE SCATTERING on translucent materials (lampshades, thin fabric)
#                 - Render accurate FRESNEL EFFECTS (reflectivity increases at glancing angles)
                
#                 SPATIAL REALISM:
#                 - Use accurate DEPTH OF FIELD with foreground/background blur gradient
#                 - Apply ATMOSPHERIC PERSPECTIVE (distant objects slightly hazed/desaturated)
#                 - Show PROPER SCALE relationships between all furniture and architectural elements
#                 - Maintain CORRECT PERSPECTIVE with vanishing points and horizon line
#                 - Add subtle LENS DISTORTION as from professional architectural photography
                
#                 COLOR & TONE:
#                 - Use REALISTIC COLOR TEMPERATURE (warm 2700-3000K for ambiance, cool 5000K+ for task)
#                 - Apply natural COLOR GRADING like high-end architectural photography
#                 - Show DYNAMIC RANGE with bright highlights and deep shadows (not overexposed/underexposed)
#                 - Include subtle COLOR CONTRAST between light and shadow areas
#                 - Add CHROMATIC ABERRATION subtly at high-contrast edges
                
#                 POST-PROCESSING EFFECTS:
#                 - Apply professional COLOR CORRECTION for magazine-quality appearance
#                 - Add slight FILM GRAIN or noise for organic, non-CG feeling
#                 - Use UNSHARP MASKING for crisp details without over-sharpening
#                 - Include subtle VIGNETTING to draw eye to center
#                 - Apply TONE MAPPING for HDR-like dynamic range
#                 """
#             else:
#                 realism_instruction = "Apply standard rendering quality with basic lighting and materials"
            
#             prompt = f"""
#             You are an ELITE ARCHITECTURAL VISUALIZATION SPECIALIST creating PHOTOREALISTIC 3D RENDERS for high-end design magazines and luxury real estate marketing.
            
#             This is VARIATION {variation + 1} of 3 - create a UNIQUE interpretation while maintaining absolute photorealism.

#             🏗️ ARCHITECTURAL FOUNDATION:
#             - {layout_instruction}
#             - Preserve structural integrity with load-bearing walls and proper construction logic
#             - Maintain realistic ceiling heights (8-12 feet typical)
#             - Keep windows and doors in architecturally sound positions
#             - Ensure proper circulation space and ergonomic clearances
            
#             {realism_instruction}

#              DESIGN AESTHETIC TRANSFORMATION:
#             {style_text}{finish_text}{theme_text}
            
#             REFERENCE IMAGE EXTRACTION:
#             Study the reference image and extract:
#             - Complete color palette with specific tones and values
#             - Material selections with accurate textures
#             - Furniture styles and proportions
#             - Decorative elements and accessories
#             - Lighting design approach
#             - Overall mood and atmosphere
            
#             Apply this aesthetic COMPLETELY to the input space while maintaining photorealistic execution.
            
#             USER INSTRUCTIONS:
#             {context if context else 'Transform this space into a stunning, photorealistic interior that could be featured in Architectural Digest or Elle Decor.'}
            
#             VARIATION STRATEGY FOR #{variation + 1}:
#             {'- Primary camera angle: slight right perspective, hero lighting from left' if variation == 0 else ''}
#             {'- Primary camera angle: centered symmetrical view, balanced lighting' if variation == 1 else ''}
#             {'- Primary camera angle: slight left perspective, hero lighting from right' if variation == 2 else ''}
            
#             FINAL QUALITY CHECK:
#             ✓ Could this render be mistaken for a professional photograph?
#             ✓ Are materials indistinguishable from reality?
#             ✓ Does lighting create authentic mood and dimension?
#             ✓ Are all details sharp, properly scaled, and believable?
#             ✓ Would a luxury design magazine publish this image?
            
#             If the answer to ANY question is no, enhance until it's yes.
            
#             OUTPUT: A FLAWLESS, PHOTOREALISTIC ARCHITECTURAL RENDER showing professional interior design execution with authentic materials, expert lighting, and impeccable attention to detail.
#             """
            
#             # Generate with optimized parameters
#             contents = [
#                 types.Content(
#                     role="user",
#                     parts=[
#                         types.Part.from_uri(file_uri=input_gemini_file.uri, mime_type=input_gemini_file.mime_type),
#                         types.Part.from_uri(file_uri=reference_gemini_file.uri, mime_type=reference_gemini_file.mime_type),
#                         types.Part.from_text(text=prompt),
#                     ],
#                 )
#             ]
            
#             # OPTIMIZED GENERATION PARAMETERS FOR REALISM
#             config = types.GenerateContentConfig(
#                 temperature=0.3 + (variation * 0.05),  # Lower temperature for consistency, slight variation
#                 top_p=0.90,  # Higher top_p for quality sampling
#                 top_k=50,  # Add top_k for better quality control
#                 max_output_tokens=8192,
#                 response_modalities=["image"],
#                 response_mime_type="text/plain",
#             )
            
#             for chunk in client.models.generate_content_stream(
#                 model="gemini-2.0-flash-exp-image-generation",
#                 contents=contents,
#                 config=config,
#             ):
#                 if (chunk.candidates and chunk.candidates[0].content and 
#                     chunk.candidates[0].content.parts and 
#                     chunk.candidates[0].content.parts[0].inline_data):
                    
#                     save_binary_file(output_filename, chunk.candidates[0].content.parts[0].inline_data.data)
#                     generated_outputs.append({
#                         'filename': output_filename,
#                         'url': f'/view_image/{os.path.basename(output_filename)}',
#                         'variation': variation + 1
#                     })
#                     break
        
#         # Store session
#         session['current_images'] = [output['filename'] for output in generated_outputs]
#         session['original_input'] = input_filename
#         session['original_reference'] = reference_filename
#         session['tweaks_used'] = 0
#         session['generation_params'] = {
#             'style': selected_style,
#             'finish': selected_finish,
#             'theme': selected_theme,
#             'context': context,
#             'preserve_layout': preserve_layout,
#             'enhance_realism': enhance_realism
#         }
        
#         return jsonify({
#             'success': True,
#             'images': [{'url': output['url'], 'variation': output['variation']} for output in generated_outputs],
#             'tweaks_remaining': 3 - session['tweaks_used'],
#             'total_generated': 3
#         })
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# @app.route('/tweak', methods=['POST'])
# def tweak_image():
#     user_id = get_user_session()
    
#     if session['tweaks_used'] >= 3:
#         return jsonify({'error': 'You have used all your tweaks for this session'}), 400
    
#     if 'current_images' not in session:
#         return jsonify({'error': 'No images to tweak. Please generate images first.'}), 400
    
#     data = request.json
#     tweak_instruction = data.get('instruction', '')
#     image_index = data.get('image_index', 0)
    
#     if not tweak_instruction:
#         return jsonify({'error': 'Tweak instruction is required'}), 400
    
#     try:
#         current_images = session['current_images']
#         if image_index >= len(current_images):
#             return jsonify({'error': 'Invalid image index'}), 400
        
#         current_image_path = current_images[image_index]
#         if not os.path.exists(current_image_path):
#             return jsonify({'error': 'Original image not found'}), 400
        
#         # Upload current image to Gemini
#         current_gemini_file = client.files.upload(file=current_image_path)
        
#         # Get generation parameters
#         params = session.get('generation_params', {})
        
#         # Create ENHANCED tweak prompt with photorealism
#         prompt = f"""
#         🔧 PROFESSIONAL ARCHITECTURAL MODIFICATION with PHOTOREALISTIC EXECUTION
        
#         You are a professional architectural renderer making PRECISE PHOTOREALISTIC modifications to this interior space.
        
#         MODIFICATION REQUEST:
#         {tweak_instruction}
        
#         🎯 PHOTOREALISTIC EXECUTION REQUIREMENTS:
        
#         LIGHTING INTEGRATION:
#         - Ensure modifications match existing lighting direction and quality
#         - Add proper shadows where new elements block light
#         - Include realistic highlights on reflective new surfaces
#         - Maintain ambient occlusion in corners and crevices
#         - Show light bounce and color bleeding from surrounding surfaces
#         - Preserve overall lighting mood and temperature
        
#         MATERIAL AUTHENTICITY:
#         - Render modifications with exact material properties:
#           * Wood: visible grain, natural color variation, appropriate sheen
#           * Metal: accurate reflections, anisotropic highlights, proper finish
#           * Fabric: texture weave, natural draping, light absorption
#           * Glass: transparency, distortion, edge highlights, reflections
#           * Paint/Plaster: slight texture, appropriate sheen level
#         - Show realistic wear and aging where appropriate
#         - Include micro-details like dust, subtle imperfections
        
#         SPATIAL INTEGRATION:
#         - Match perspective and vanishing points exactly
#         - Maintain accurate scale relative to existing elements
#         - Show proper depth of field matching the original
#         - Include appropriate atmospheric effects
#         - Ensure modifications respect architectural logic
        
#         CONSISTENCY MAINTENANCE:
#         - Preserve overall {params.get('style', 'current')} style aesthetic
#         - Maintain {params.get('finish', 'current')} surface finish quality throughout
#         - Keep faithful to {params.get('theme', 'current')} room function and purpose
#         - Match color temperature and grading of original image
#         - Ensure modifications enhance rather than detract from design unity
        
#         QUALITY STANDARDS:
#         - Modifications must be INDISTINGUISHABLE from reality
#         - Seamlessly blend with unmodified portions of image
#         - Maintain magazine-quality architectural photography appearance
#         - Show professional craftsmanship in execution
#         - Include appropriate shadows, reflections, and light interaction
        
#         THREE-DIMENSIONAL REALISM:
#         - Create authentic depth and volume, not flat surface changes
#         - Show proper thickness of materials (walls, countertops, etc.)
#         - Include edge details and transitions between materials
#         - Render realistic joinery and construction methods
#         - Add subtle imperfections that make it look real and built
        
#         Execute this modification with FLAWLESS PHOTOREALISTIC PRECISION, creating a result that could be a professional photograph rather than a render.
#         """
        
#         # Prepare content for tweaking
#         contents = [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_uri(file_uri=current_gemini_file.uri, mime_type=current_gemini_file.mime_type),
#                     types.Part.from_text(text=prompt),
#                 ],
#             )
#         ]
        
#         # OPTIMIZED generation config for precise, realistic modifications
#         config = types.GenerateContentConfig(
#             temperature=0.25,  # Very low temperature for precise, controlled modifications
#             top_p=0.85,
#             top_k=40,
#             max_output_tokens=8192,
#             response_modalities=["image"],
#             response_mime_type="image/jpeg",
#         )
        
#         # Generate tweaked image
#         tweaked_filename = f"generated/{user_id}_tweaked_{image_index}_{uuid.uuid4().hex[:8]}.jpg"
        
#         image_generated = False
#         for chunk in client.models.generate_content_stream(
#             model="gemini-2.0-flash-exp-image-generation",
#             contents=contents,
#             config=config,
#         ):
#             if (chunk.candidates and chunk.candidates[0].content and 
#                 chunk.candidates[0].content.parts and 
#                 chunk.candidates[0].content.parts[0].inline_data):
                
#                 save_binary_file(tweaked_filename, chunk.candidates[0].content.parts[0].inline_data.data)
                
#                 # Update session
#                 session['current_images'][image_index] = tweaked_filename
#                 session['tweaks_used'] += 1
                
#                 image_generated = True
#                 break
        
#         if image_generated:
#             return jsonify({
#                 'success': True,
#                 'image_url': f'/view_image/{os.path.basename(tweaked_filename)}',
#                 'tweaks_remaining': 3 - session['tweaks_used'],
#                 'image_index': image_index,
#             })
#         else:
#             return jsonify({'error': 'No tweaked image generated'}), 500
        
#     except Exception as e:
#         print(f"Error in tweak_image: {str(e)}")
#         return jsonify({'error': str(e)}), 500


# @app.route('/view_image/<filename>')
# def view_image(filename):
#     print("Trying to load:", filename)
#     file_path = f'generated/{filename}'
#     if not os.path.exists(file_path):
#         return jsonify({'error': 'File not found'}), 404
#     return send_file(file_path)


# @app.route('/download_image')
# def download_image():
#     image_index = request.args.get('index', 0, type=int)
    
#     if 'current_images' not in session:
#         return jsonify({'error': 'No images to download'}), 400
    
#     current_images = session['current_images']
#     if image_index >= len(current_images):
#         return jsonify({'error': 'Invalid image index'}), 400
    
#     current_image_path = current_images[image_index]
#     if not os.path.exists(current_image_path):
#         return jsonify({'error': 'Image file not found'}), 400
    
#     variation_number = image_index + 1
#     return send_file(current_image_path, as_attachment=True, 
#                 download_name=f'photorealistic_render_v{variation_number}.jpg')

# @app.route('/download_all')
# def download_all():
#     if 'current_images' not in session:
#         return jsonify({'error': 'No images to download'}), 400
    
#     import zipfile
#     import tempfile
    
#     current_images = session['current_images']
    
#     # Create temporary zip file
#     temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
#     with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
#         for i, image_path in enumerate(current_images):
#             if os.path.exists(image_path):
#                 zipf.write(image_path, f'photorealistic_render_v{i + 1}.jpg')    
    
#     return send_file(temp_zip.name, as_attachment=True, 
#                     download_name='photorealistic_interior_renders.zip')

# @app.route('/reset_session')
# def reset_session():
#     session.clear()
#     return jsonify({'success': True, 'message': 'Session reset successfully'})

# @app.route('/')
# def index():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)

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
    
    # Get form data
    context = request.form.get('context', '').strip()
    selected_style = request.form.get('style', '').strip() or None
    selected_finish = request.form.get('finish', '').strip() or None
    selected_theme = request.form.get('theme', '').strip() or None
    preserve_layout = request.form.get('preserve_layout', 'true') == 'true'
    enhance_realism = request.form.get('enhance_realism', 'true') == 'true'
    
    # Get uploaded files
    input_files = request.files.getlist('input_images')
    reference_files = request.files.getlist('reference_images')
    
    # Validation
    if len(input_files) != 1 or len(reference_files) != 1:
        return jsonify({'error': 'Please upload exactly 1 input image and 1 reference image'}), 400
    
    input_file = input_files[0]
    reference_file = reference_files[0]
    
    if not allowed_file(input_file.filename) or not allowed_file(reference_file.filename):
        return jsonify({'error': 'Only PNG, JPG, JPEG files allowed'}), 400
    
    try:
        # Save and upload files
        input_filename = f"uploads/input/{user_id}_input_{uuid.uuid4().hex[:8]}.jpg"
        reference_filename = f"uploads/reference/{user_id}_reference_{uuid.uuid4().hex[:8]}.jpg"
        
        input_file.save(input_filename)
        reference_file.save(reference_filename)
        
        input_gemini_file = client.files.upload(file=input_filename)
        reference_gemini_file = client.files.upload(file=reference_filename)
        
        # Generate 3 variations
        generated_outputs = []
        
        for variation in range(3):
            output_filename = f"generated/{user_id}_output_{variation}_{uuid.uuid4().hex[:8]}.jpg"
            
            # Build prompt (use your existing single transformation prompt)
            style_text = f"- Style: {selected_style.title()} - {get_style_description(selected_style)}\n" if selected_style else ""
            finish_text = f"- Finish: {selected_finish.title()} - {get_finish_description(selected_finish)}\n" if selected_finish else ""
            theme_text = f"- Theme: {selected_theme.title()} - {get_theme_description(selected_theme)}\n" if selected_theme else "- Theme: Auto-detect room type\n"
            
            layout_instruction = "CRITICAL: Maintain the EXACT room proportions and spatial layout" if preserve_layout else "You may adjust room proportions if needed"
            realism_instruction = "Apply enhanced photorealistic rendering with professional lighting" if enhance_realism else "Apply standard rendering quality"
            
            prompt = f"""
            You are a PROFESSIONAL ARCHITECTURAL RENDERER (Variation {variation + 1}/3).

            🏗️ ARCHITECTURAL REQUIREMENTS:
            - {layout_instruction}
            - {realism_instruction}
            - Preserve structural integrity and realistic elements
            - Create authentic material textures with depth

            🎨 DESIGN TRANSFORMATION:
            {style_text}{finish_text}{theme_text}

            Extract complete design aesthetic from reference while maintaining input architecture.
            
            {context if context else 'Create a professional rendering with complete aesthetic transformation.'}
            
            Generate variation {variation + 1} with unique design details while staying true to the reference style.
            """
            
            # Generate (use existing generation code)
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(file_uri=input_gemini_file.uri, mime_type=input_gemini_file.mime_type),
                        types.Part.from_uri(file_uri=reference_gemini_file.uri, mime_type=reference_gemini_file.mime_type),
                        types.Part.from_text(text=prompt),
                    ],
                )
            ]
            
            config = types.GenerateContentConfig(
                temperature=0.5 + (variation * 0.1),  # Slight variation
                top_p=0.85,
                max_output_tokens=8192,
                response_modalities=["image", "text"],
                response_mime_type="text/plain",
            )
            
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
                        'variation': variation + 1
                    })
                    break
        
        # Store session
        session['current_images'] = [output['filename'] for output in generated_outputs]
        session['original_input'] = input_filename
        session['original_reference'] = reference_filename
        session['tweaks_used'] = 0
        session['generation_params'] = {
            'style': selected_style,
            'finish': selected_finish,
            'theme': selected_theme,
            'context': context,
            'preserve_layout': preserve_layout,
            'enhance_realism': enhance_realism
        }
        
        return jsonify({
            'success': True,
            'images': [{'url': output['url'], 'variation': output['variation']} for output in generated_outputs],
            'tweaks_remaining': 3 - session['tweaks_used'],
            'total_generated': 3
        })
        
    except Exception as e:
        # Error handling (keep existing)
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
        
        # Get generation parameters
        params = session.get('generation_params', {})
        
        # Create tweak prompt
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
        - Maintain the overall {params.get('style', 'current')} style consistency
        - Preserve {params.get('finish', 'current')} surface finish quality  
        - Keep true to the {params.get('theme', 'current')} room function
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
        
        # Generation config for precise modifications
        config = types.GenerateContentConfig(
            temperature=0.4,  # Low temperature for precise modifications
            top_p=0.8,
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
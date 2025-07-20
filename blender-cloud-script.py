import bpy
import math
import random

# 씬 초기화
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 렌더링 설정
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.film_transparent = True
bpy.context.scene.cycles.samples = 128
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 250
bpy.context.scene.render.fps = 24

# 월드 설정 - 하늘색 배경
world = bpy.context.scene.world
world.use_nodes = True
world_nodes = world.node_tree.nodes
world_links = world.node_tree.links

# 기존 노드 제거
for node in world_nodes:
    world_nodes.remove(node)

# 새 노드 추가
bg_node = world_nodes.new('ShaderNodeBackground')
bg_node.inputs[0].default_value = (0.5, 0.7, 0.9, 1.0)  # 하늘색
bg_node.inputs[1].default_value = 1.0

output_node = world_nodes.new('ShaderNodeOutputWorld')
world_links.new(bg_node.outputs[0], output_node.inputs[0])

# 카메라 설정
bpy.ops.object.camera_add(location=(0, -7, 2), rotation=(math.radians(80), 0, 0))
camera = bpy.context.active_object
bpy.context.scene.camera = camera

# 주 광원 (태양) 추가
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0

# 구름 만들기 함수
def create_cloud(location, scale, is_main_character=False):
    # 메타볼 컬렉션 생성
    metaball = bpy.data.metaballs.new("CloudMeta")
    metaball_obj = bpy.data.objects.new("Cloud", metaball)
    bpy.context.collection.objects.link(metaball_obj)
    
    # 메타볼 설정
    metaball.resolution = 0.2
    metaball.render_resolution = 0.05
    
    # 랜덤 구체 개수 (더 복잡한 구름 형태를 위해)
    num_elements = random.randint(6, 12)
    
    # 메타볼 요소 생성
    elements = []
    for i in range(num_elements):
        # 중앙에 가까운 랜덤 위치
        x_offset = random.uniform(-1.0, 1.0) * scale[0]
        y_offset = random.uniform(-0.7, 0.7) * scale[1]
        z_offset = random.uniform(-0.5, 0.5) * scale[2]
        
        # 크기도 약간씩 변화
        radius = random.uniform(0.8, 1.5)
        
        # 새 메타볼 생성
        element = metaball.elements.new()
        element.radius = radius
        element.co = (x_offset, y_offset, z_offset)
        elements.append(element)
    
    # 오브젝트 위치와 스케일 설정
    metaball_obj.location = location
    metaball_obj.scale = scale
    
    # 머티리얼 생성 및 적용
    mat = bpy.data.materials.new("CloudMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 기존 노드 제거
    for node in nodes:
        nodes.remove(node)
    
    # 볼륨 산란 (구름 효과)
    volume_scatter = nodes.new(type='ShaderNodeVolumeScatter')
    volume_scatter.inputs['Density'].default_value = 5.0
    volume_scatter.inputs['Anisotropy'].default_value = 0.3
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(volume_scatter.outputs['Volume'], output.inputs['Volume'])
    
    # 주인공 구름인 경우 표정 추가
    if is_main_character:
        # 메타볼을 메시로 변환하기 위해 일단 활성화
        bpy.context.view_layer.objects.active = metaball_obj
        
        # 메시로 변환 (이후 표정 추가를 위해)
        bpy.ops.object.convert(target='MESH')
        
        # 눈 만들기 (두 개의 구)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(location[0]-0.5, location[1]-0.5, location[2]+0.5))
        left_eye = bpy.context.active_object
        left_eye.name = "LeftEye"
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(location[0]+0.5, location[1]-0.5, location[2]+0.5))
        right_eye = bpy.context.active_object
        right_eye.name = "RightEye"
        
        # 눈 머티리얼 생성
        eye_mat = bpy.data.materials.new("EyeMaterial")
        eye_mat.use_nodes = True
        eye_nodes = eye_mat.node_tree.nodes
        
        for node in eye_nodes:
            if node.type == 'BSDF_PRINCIPLED':
                node.inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)
                node.inputs['Specular'].default_value = 0.8
        
        left_eye.data.materials.append(eye_mat)
        right_eye.data.materials.append(eye_mat)
        
        # 미소 만들기 (커브)
        bpy.ops.curve.primitive_bezier_curve_add(location=(location[0], location[1]-0.5, location[2]))
        smile = bpy.context.active_object
        smile.name = "Smile"
        
        # 커브 포인트 조정하여 미소 만들기
        curve_data = smile.data
        for point in curve_data.splines[0].bezier_points:
            point.handle_left_type = 'AUTO'
            point.handle_right_type = 'AUTO'
        
        # 첫 번째 및 마지막 포인트 위치 설정
        curve_data.splines[0].bezier_points[0].co = (-0.5, 0, 0)
        curve_data.splines[0].bezier_points[1].co = (0.5, 0, 0)
        
        # 중간 점 추가 및 위치 설정
        curve_data.splines[0].bezier_points.add(1)
        curve_data.splines[0].bezier_points[1].co = (0, -0.3, 0)
        
        # 커브 두께 조정
        curve_data.bevel_depth = 0.05
        
        # 커브 머티리얼 생성
        curve_mat = bpy.data.materials.new("SmileMaterial")
        curve_mat.use_nodes = True
        curve_nodes = curve_mat.node_tree.nodes
        
        for node in curve_nodes:
            if node.type == 'BSDF_PRINCIPLED':
                node.inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)
        
        smile.data.materials.append(curve_mat)
        
        # 눈과 미소를 구름에 페어런팅
        left_eye.parent = metaball_obj
        right_eye.parent = metaball_obj
        smile.parent = metaball_obj
        
        # 애니메이션 추가 - 위아래 움직임
        metaball_obj.animation_data_create()
        metaball_obj.animation_data.action = bpy.data.actions.new("CloudAction")
        
        # Z 위치 키프레임 설정
        z_fcurve = metaball_obj.animation_data.action.fcurves.new("location", index=2)
        
        # 사인파로 부드러운 애니메이션 생성
        mod = z_fcurve.modifiers.new('CYCLES')
        mod.mode_before = 'REPEAT'
        mod.mode_after = 'REPEAT'
        
        # 키프레임 설정
        kf1 = z_fcurve.keyframe_points.insert(frame=1, value=location[2])
        kf2 = z_fcurve.keyframe_points.insert(frame=60, value=location[2] + 0.5)
        kf3 = z_fcurve.keyframe_points.insert(frame=120, value=location[2])
        
        # 눈 깜빡임 애니메이션
        for eye in [left_eye, right_eye]:
            eye.animation_data_create()
            eye.animation_data.action = bpy.data.actions.new(f"{eye.name}Action")
            
            # Y 스케일 키프레임으로 깜빡임 효과
            y_fcurve = eye.animation_data.action.fcurves.new("scale", index=1)
            
            # 키프레임 설정 (120프레임마다 깜빡임)
            y_fcurve.keyframe_points.insert(frame=1, value=1.0)
            y_fcurve.keyframe_points.insert(frame=60, value=0.1)
            y_fcurve.keyframe_points.insert(frame=70, value=1.0)
            y_fcurve.keyframe_points.insert(frame=180, value=1.0)
            y_fcurve.keyframe_points.insert(frame=190, value=0.1)
            y_fcurve.keyframe_points.insert(frame=200, value=1.0)
    
    # 완성된 구름 오브젝트 반환
    return metaball_obj

# 비 입자 효과 생성 함수
def create_rain(cloud_obj):
    # 비 파티클 시스템 생성
    bpy.context.view_layer.objects.active = cloud_obj
    bpy.ops.object.particle_system_add()
    
    particle_system = cloud_obj.particle_systems[-1]
    particle_settings = particle_system.settings
    
    # 파티클 시스템 설정
    particle_settings.name = "Rain"
    particle_settings.type = 'HAIR'
    particle_settings.count = 2000  # 빗방울 수
    particle_settings.hair_length = 2.0  # 빗줄기 길이
    particle_settings.lifetime = 50  # 빗방울 지속 시간
    
    # 물리 효과 - 중력의 영향을 받음
    particle_settings.physics_type = 'NEWTON'
    # 더 무거운 빗방울
    particle_settings.mass = 2.0
    
    # 방출 설정
    particle_settings.emit_from = 'VOLUME'  # 볼륨에서 방출
    particle_settings.use_emit_random = True
    particle_settings.frame_start = 1
    particle_settings.frame_end = 2
    particle_settings.lifetime_random = 0.5
    
    # 렌더링 설정
    particle_settings.render_type = 'OBJECT'
    
    # 빗방울 모양의 객체 생성
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.02)
    raindrop = bpy.context.active_object
    raindrop.name = "Raindrop"
    
    # 빗방울 모양 늘이기
    bpy.ops.transform.resize(value=(1, 1, 2))
    
    # 빗방울 머티리얼 생성
    rain_mat = bpy.data.materials.new("RainMaterial")
    rain_mat.use_nodes = True
    rain_nodes = rain_mat.node_tree.nodes
    rain_links = rain_mat.node_tree.links
    
    # 기존 노드 제거
    for node in rain_nodes:
        rain_nodes.remove(node)
    
    # 유리 셰이더 설정
    glass = rain_nodes.new('ShaderNodeBsdfGlass')
    glass.inputs['Color'].default_value = (0.8, 0.9, 1.0, 1.0)
    glass.inputs['Roughness'].default_value = 0.0
    glass.inputs['IOR'].default_value = 1.33  # 물의 굴절률
    
    output = rain_nodes.new('ShaderNodeOutputMaterial')
    rain_links.new(glass.outputs[0], output.inputs[0])
    
    raindrop.data.materials.append(rain_mat)
    
    # 빗방울을 파티클로 지정
    particle_settings.instance_object = raindrop
    
    # 빗방울 객체는 렌더링에서 숨김
    raindrop.hide_render = True

# 무지개 생성 함수
def create_rainbow(location):
    # 베지어 커브로 반원 생성
    bpy.ops.curve.primitive_bezier_curve_add(location=location)
    rainbow = bpy.context.active_object
    rainbow.name = "Rainbow"
    
    # 커브 모양 설정
    curve_data = rainbow.data
    curve_data.dimensions = '3D'
    
    # 베지어 포인트 조정
    points = curve_data.splines[0].bezier_points
    points[0].co = (-4, 0, 0)
    points[0].handle_left = (-4, -2, 0)
    points[0].handle_right = (-4, 2, 0)
    
    points[1].co = (4, 0, 0)
    points[1].handle_left = (4, 2, 0)
    points[1].handle_right = (4, -2, 0)
    
    # 중간 점 추가
    curve_data.splines[0].bezier_points.add(1)
    points[1].co = (0, 0, 2)
    points[1].handle_left = (-2, 0, 2)
    points[1].handle_right = (2, 0, 2)
    
    # 커브를 두껍게 만들기
    curve_data.bevel_depth = 0.1
    
    # 무지개 머티리얼 생성
    mat = bpy.data.materials.new("RainbowMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 기존 노드 제거
    for node in nodes:
        nodes.remove(node)
    
    # 컬러 램프 노드로 무지개 색상 생성
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.color_ramp.elements.remove(color_ramp.color_ramp.elements[0])
    
    # 무지개 색상 설정 (7색)
    colors = [
        (0.0, (1.0, 0.0, 0.0, 1.0)),  # 빨강
        (0.16, (1.0, 0.5, 0.0, 1.0)),  # 주황
        (0.33, (1.0, 1.0, 0.0, 1.0)),  # 노랑
        (0.5, (0.0, 1.0, 0.0, 1.0)),   # 초록
        (0.66, (0.0, 0.0, 1.0, 1.0)),  # 파랑
        (0.83, (0.3, 0.0, 0.5, 1.0)),  # 남색
        (1.0, (0.5, 0.0, 1.0, 1.0))    # 보라
    ]
    
    # 첫 번째 색상
    color_ramp.color_ramp.elements[0].position = colors[0][0]
    color_ramp.color_ramp.elements[0].color = colors[0][1]
    
    # 나머지 색상 추가
    for pos, color in colors[1:]:
        element = color_ramp.color_ramp.elements.new(pos)
        element.color = color
    
    # 텍스처 좌표 노드 추가
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    
    # Mapping 노드로 UV 조정
    mapping = nodes.new(type='ShaderNodeMapping')
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    
    # 그라데이션 텍스처 노드
    gradient = nodes.new(type='ShaderNodeTexGradient')
    gradient.gradient_type = 'LINEAR'
    links.new(mapping.outputs['Vector'], gradient.inputs['Vector'])
    
    # 그라데이션을 컬러 램프에 연결
    links.new(gradient.outputs['Color'], color_ramp.inputs['Fac'])
    
    # 방출 셰이더로 빛나는 효과
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs['Strength'].default_value = 2.0
    links.new(color_ramp.outputs['Color'], emission.inputs['Color'])
    
    # 출력 노드에 연결
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    # 머티리얼 적용
    rainbow.data.materials.append(mat)
    
    # 애니메이션 - 페이드 인/아웃
    rainbow.animation_data_create()
    rainbow.animation_data.action = bpy.data.actions.new("RainbowAction")
    
    # 투명도(알파) 키프레임 설정
    alpha_fcurve = rainbow.animation_data.action.fcurves.new("hide_render")
    
    # 키프레임 추가
    alpha_fcurve.keyframe_points.insert(frame=1, value=1)  # 처음에는 숨김
    alpha_fcurve.keyframe_points.insert(frame=100, value=0)  # 서서히 나타남
    alpha_fcurve.keyframe_points.insert(frame=200, value=0)  # 유지
    alpha_fcurve.keyframe_points.insert(frame=250, value=1)  # 서서히 사라짐
    
    return rainbow

# 주요 구름 생성
main_cloud = create_cloud(location=(0, 0, 2), scale=(2, 2, 1), is_main_character=True)

# 작은 구름들 여러 개 추가
cloud_positions = [
    (-4, -2, 3),
    (4, -3, 2.5),
    (-3, 2, 3.5),
    (3, 3, 2.8)
]

# 작은 구름들 생성
for pos in cloud_positions:
    # 랜덤한 크기
    scale_factor = random.uniform(0.7, 1.3)
    cloud = create_cloud(location=pos, scale=(scale_factor, scale_factor, scale_factor * 0.5))
    
    # 간단한 위치 애니메이션
    cloud.animation_data_create()
    cloud.animation_data.action = bpy.data.actions.new(f"Cloud{pos}Action")
    
    # X 위치 키프레임 설정 - 좌우 움직임
    x_fcurve = cloud.animation_data.action.fcurves.new("location", index=0)
    
    # 키프레임 추가
    x_fcurve.keyframe_points.insert(frame=1, value=pos[0])
    x_fcurve.keyframe_points.insert(frame=125, value=pos[0] + random.uniform(-1, 1))
    x_fcurve.keyframe_points.insert(frame=250, value=pos[0])

# 비 효과 추가
create_rain(main_cloud)

# 무지개 추가
create_rainbow(location=(0, -2, 0))

# 렌더링 경로 설정
bpy.context.scene.render.filepath = "//cloud_animation.mp4"
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'
bpy.context.scene.render.ffmpeg.codec = 'H264'

# 뷰포트 설정 (시각적으로 보기 좋게)
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'
                break

print("구름 애니메이션 씬 생성이 완료되었습니다!")

import * as THREE from 'https://unpkg.com/three@0.125.0/build/three.module.js';
import { OrbitControls } from 'https://unpkg.com/three@0.125.0/examples/jsm/controls/OrbitControls.js';
      
let container;

let camera, controls, scene, renderer;

let mesh, texture;

let helper;

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

// TODO set default values here
const nx0 = 20, ny0 = 20;
const elev0 = new Uint8Array(nx0*ny0);
elev0.fill(100.0);
init(nx0, ny0, 1000, 1000, elev0, 1.0, 1.0, 0.0, 0.0);
animate();

function init(nx, ny, long_dist, lat_dist, elev, tex_scale_x, tex_scale_y,
              tex_shift_x, tex_shift_y, image_url, path) {
  container = document.getElementById('terrain_container');
  container.innerHTML = '';

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  container.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);

  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 100, 200000);
 
  // skip drawing if user hasn't run pathfinder 
  if (typeof image_url == 'undefined') {
    return;
  }

  controls = new OrbitControls(camera, renderer.domElement);
  controls.minDistance = Math.max(lat_dist, long_dist);
  controls.maxDistance = 10.0 * controls.minDistance;
  controls.maxPolarAngle = Math.PI / 2;

  // TODO: set initial camera position
  const half_nx = nx / 2, half_ny = ny / 2;
  controls.target.y = elev[half_nx + half_ny * nx] + 100;
  camera.position.y = controls.target.y + 100;
  camera.position.x = 100;
  controls.update();

  const geometry = new THREE.PlaneGeometry(long_dist, lat_dist, nx-1, ny-1);
  geometry.rotateX(-Math.PI / 2);

  const vertical_scale = 10.0;
  const vertices = geometry.attributes.position.array;
  for (let i = 0, j = 0, l = vertices.length; i < l; i ++, j += 3) {
    vertices[j + 1] = vertical_scale * elev[i];
  }
  geometry.computeVertexNormals();

  texture = new THREE.TextureLoader().load(image_url);
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  
  // scale and translate texture to line up with the edges of the map
  texture.repeat.set(tex_scale_x, tex_scale_y);
  texture.offset.set(tex_shift_x, tex_shift_y);

  mesh = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial({ map: texture }));
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);

  // draw the optimal path
  let points = [];
  for (let n = 0; n < path.length/2; n++) {
    let i = path[2*n];
    let j = path[2*n+1];
    points.push(new THREE.Vector3(((i+0.5)/nx-0.5) * long_dist,
      1.1*vertical_scale*elev[nx*j + i],
      ((j+0.5)/ny-0.5) * lat_dist));
  }
  const tube_curve = new THREE.CatmullRomCurve3(points);
  const tube_thick = Math.sqrt(lat_dist*lat_dist + long_dist*long_dist)/300.0;
  const tube_geometry = new THREE.TubeGeometry(tube_curve, nx+ny, tube_thick, 10, false);
  const material = new THREE.MeshPhongMaterial({color: 0xff0000});
  const tube_mesh = new THREE.Mesh(tube_geometry, material);
  scene.add(tube_mesh);

  // create a directional light and turn on shadows
  const light = new THREE.DirectionalLight(0xffffff, 1.0, 100);
  light.position.set(1.0, 1.0, 0);
  light.castShadow = true;
  scene.add(light);

  // TODO: fix shadow parameters
	light.shadow.mapSize.width = 2048;
	light.shadow.mapSize.height = 2048;
	light.shadow.camera.near = 200;
	light.shadow.camera.far = 1500;
	light.shadow.camera.fov = 40;
	light.shadow.bias = - 0.005;

  // TODO: remove geometryHelper
  const geometryHelper = new THREE.ConeGeometry(20, 100, 3);
  geometryHelper.translate(0, 50, 0);
  geometryHelper.rotateX(Math.PI / 2);
  helper = new THREE.Mesh(geometryHelper, new THREE.MeshNormalMaterial());
  scene.add(helper);

  container.addEventListener('pointermove', onPointerMove);

  window.addEventListener('resize', onWindowResize);
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();

  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  render();
}

function render() {
  renderer.render(scene, camera);
}

function onPointerMove(event) {
  pointer.x = ((event.clientX - renderer.domElement.offsetLeft) / renderer.domElement.clientWidth) * 2 - 1;
  pointer.y = - ((event.clientY - renderer.domElement.offsetTop) / renderer.domElement.clientHeight) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);

  // See if the ray from the camera into the world hits one of our meshes
  const intersects = raycaster.intersectObject(mesh);

  // Toggle rotation bool for meshes that we clicked
  if (intersects.length > 0) {
    helper.position.set(0, 0, 0);
    helper.lookAt(intersects[0].face.normal);

    helper.position.copy(intersects[0].point);
  }
}

// function to update terrain and texture data
export function update(response) {
  if (response.result == 2) {
    alert("Invalid Starting Location");
  }
  else if (response.result == 3) {
    alert("Invalid Ending Location");
  }
  else if (response.result == 4) {
    alert("No Valid Path Between Start and End");
  }
  init(response.nx, response.ny, response.long_dist, response.lat_dist, 
    response.elev, response.tex_scale_x, response.tex_scale_y, 
    response.tex_shift_x, response.tex_shift_y, response.image_url, 
    response.path);
}


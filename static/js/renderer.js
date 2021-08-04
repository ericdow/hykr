import * as THREE from 'https://unpkg.com/three/build/three.module.js';
import { OrbitControls } from './OrbitControls.js';
import { ImprovedNoise } from 'https://unpkg.com/three/examples/jsm/math/ImprovedNoise.js';
      
let container;

let camera, controls, scene, renderer;

let mesh, texture;

let helper;

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

// TODO add directional light

// TODO set default values here
const nx0 = 20, ny0 = 20;
const elev0 = new Uint8Array(nx0*ny0);
elev0.fill(100.0);
init(nx0, ny0, 1000, 1000, elev0);
animate();

function init(nx, ny, long_dist, lat_dist, elev, image_url) {
  container = document.getElementById('terrain_container');
  container.innerHTML = '';

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  container.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);

  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 100, 200000);

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

  geometry.computeFaceNormals(); // needed for helper

  // TODO: only set texture if URL is present
  texture = new THREE.TextureLoader().load(image_url)
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  
  // scale and translate texture to line up with the edges of the map
  // TODO
  // texture.repeat.set(0.5, 0.5);

  mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ map: texture }));
  scene.add(mesh);

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
  pointer.x = (event.clientX / renderer.domElement.clientWidth) * 2 - 1;
  pointer.y = - (event.clientY / renderer.domElement.clientHeight) * 2 + 1;
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
  init(response.nx, response.ny, response.long_dist, response.lat_dist, 
      response.elev, response.image_url);
}


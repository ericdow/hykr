import * as THREE from 'https://unpkg.com/three/build/three.module.js';
import { OrbitControls } from './OrbitControls.js';
import { ImprovedNoise } from 'https://unpkg.com/three/examples/jsm/math/ImprovedNoise.js';
			
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
init(nx0, ny0, 1000, 1000, elev0);
animate();

function init(nx, ny, long_dist, lat_dist, elev) {
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

  // TODO: this is where to set the texture data
	texture = new THREE.CanvasTexture(generateTexture(elev, nx, ny));
	texture.wrapS = THREE.ClampToEdgeWrapping;
	texture.wrapT = THREE.ClampToEdgeWrapping;

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

function generateHeight(width, height) {
	const size = width * height, data = new Uint8Array(size),
		perlin = new ImprovedNoise(), z = Math.random() * 100;

	let quality = 1;

	for (let j = 0; j < 4; j ++) {

		for (let i = 0; i < size; i ++) {

			const x = i % width, y = ~ ~ (i / width);
			data[ i ] += Math.abs(perlin.noise(x / quality, y / quality, z) * quality * 1.75);

		}

		quality *= 5;

	}

	return data;
}

function generateTexture(data, width, height) {
	// bake lighting into texture
	let context, image, imageData, shade;

	const vector3 = new THREE.Vector3(0, 0, 0);

	const sun = new THREE.Vector3(1, 1, 1);
	sun.normalize();

	const canvas = document.createElement('canvas');
	canvas.width = width;
	canvas.height = height;

	context = canvas.getContext('2d');
	context.fillStyle = '#000';
	context.fillRect(0, 0, width, height);

	image = context.getImageData(0, 0, canvas.width, canvas.height);
	imageData = image.data;

	for (let i = 0, j = 0, l = imageData.length; i < l; i += 4, j ++) {

		vector3.x = data[ j - 2 ] - data[ j + 2 ];
		vector3.y = 2;
		vector3.z = data[ j - width * 2 ] - data[ j + width * 2 ];
		vector3.normalize();

		shade = vector3.dot(sun);

		imageData[ i ] = (96 + shade * 128) * (0.5 + data[ j ] * 0.007);
		imageData[ i + 1 ] = (32 + shade * 96) * (0.5 + data[ j ] * 0.007);
		imageData[ i + 2 ] = (shade * 96) * (0.5 + data[ j ] * 0.007);

	}

	context.putImageData(image, 0, 0);

	// Scaled 4x

	const canvasScaled = document.createElement('canvas');
	canvasScaled.width = width * 4;
	canvasScaled.height = height * 4;

	context = canvasScaled.getContext('2d');
	context.scale(4, 4);
	context.drawImage(canvas, 0, 0);

	image = context.getImageData(0, 0, canvasScaled.width, canvasScaled.height);
	imageData = image.data;

	for (let i = 0, l = imageData.length; i < l; i += 4) {

		const v = ~ ~ (Math.random() * 5);

		imageData[ i ] += v;
		imageData[ i + 1 ] += v;
		imageData[ i + 2 ] += v;

	}

	context.putImageData(image, 0, 0);

	return canvasScaled;
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
      response.elev);
}


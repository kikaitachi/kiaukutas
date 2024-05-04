import * as THREE from "https://esm.sh/three@0.164.1";
import { OrbitControls } from 'https://esm.sh/three@0.164.1/addons/controls/OrbitControls.js';
import { STLLoader } from 'https://esm.sh/three@0.164.1/addons/loaders/STLLoader.js';
import URDFLoader from "https://esm.sh/urdf-loader@0.12.1";

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
directionalLight.castShadow = true;
directionalLight.shadow.mapSize.setScalar(1024);
directionalLight.position.set(5, 30, 5);
scene.add(directionalLight);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
scene.add(ambientLight);

camera.position.z = 50;

function animate() {
	requestAnimationFrame(animate);
	renderer.render(scene, camera);
}
animate();

const manager = new THREE.LoadingManager();
const loader = new URDFLoader(manager);

const ground = new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.ShadowMaterial({ opacity: 0.25 }));
ground.rotation.x = -Math.PI / 2;
ground.scale.setScalar(30);
ground.receiveShadow = true;
scene.add(ground);

const meshes = [];

loader.loadMeshCb = (path, manager, onComplete) => {
  new STLLoader(manager).load(
    path,
    result => {
        const material = new THREE.MeshPhongMaterial();
        const mesh = new THREE.Mesh(result, material);
        meshes.push(mesh);
        onComplete(mesh);
    }
  );
};

loader.load(
  "robot.urdf",
  robot => {
    scene.add(robot);
  }
);

document.addEventListener("mousedown", (event) => {
  event.preventDefault();
  const mouse3D = new THREE.Vector3(
    (event.clientX / window.innerWidth) * 2 - 1,
    -(event.clientY / window.innerHeight) * 2 + 1,
    0.5);
  const raycaster = new THREE.Raycaster();
  raycaster.setFromCamera(mouse3D, camera);
  const intersects = raycaster.intersectObjects(meshes);
  if (intersects.length > 0) {
    intersects[0].object.material.color.setHex(Math.random() * 0xffffff);
  }
});

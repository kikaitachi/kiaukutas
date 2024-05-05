import * as THREE from "https://esm.sh/three@0.164.1";
import { TrackballControls } from 'https://esm.sh/three@0.164.1/addons/controls/TrackballControls.js';
import { STLLoader } from 'https://esm.sh/three@0.164.1/addons/loaders/STLLoader.js';
import URDFLoader from "https://esm.sh/urdf-loader@0.12.1";

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x263238);
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 10000);

const renderer = new THREE.WebGLRenderer({
  antialias: true,
});
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new TrackballControls(camera, renderer.domElement);
controls.rotateSpeed = 2.0;

const backLight = new THREE.DirectionalLight(0xffffff, 1.0);
backLight.position.set(0, 1000, 0);
scene.add(backLight);

const frontLight = new THREE.DirectionalLight(0xffffff, 1.0);
frontLight.position.set(0, -1000, 0);
scene.add(frontLight);

const ambientLight = new THREE.AmbientLight(0xffffff, 1);
scene.add(ambientLight);

camera.position.z = 400;

function animate() {
	requestAnimationFrame(animate);
  controls.update();
	renderer.render(scene, camera);
}
animate();

const manager = new THREE.LoadingManager();
const loader = new URDFLoader(manager);

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(250, 128),
  new THREE.MeshPhysicalMaterial({
    opacity: 0.5,
    transparent: true,
    side: THREE.DoubleSide,
  })
);
scene.add(ground);

const meshes = [];

const get_part_material = (part) => {
  if (part.endsWith("shaft.stl")) {
    console.log("shaft");
    return new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0,
    });
  }
  if (part.endsWith("XM430-W350-T.stl")) {
    console.log("dynamixel");
    return new THREE.MeshBasicMaterial({
      color: 0x100000,
    });
  }
  return new THREE.MeshPhongMaterial();
};

loader.loadMeshCb = (path, manager, onComplete) => {
  console.log(`Loading: ${path}`);
  new STLLoader(manager).load(
    path,
    result => {
        console.log(`Loaded: ${path}`);
        const mesh = new THREE.Mesh(result, new THREE.MeshPhongMaterial());
        meshes.push(mesh);
        onComplete(mesh);
        //mesh.material = get_part_material(path);
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
    //intersects[0].object.material.color.setHex(Math.random() * 0xffffff);
  }
});

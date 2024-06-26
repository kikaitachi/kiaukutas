import * as THREE from 'https://esm.sh/three@0.164.1'
import { TrackballControls } from 'https://esm.sh/three@0.164.1/addons/controls/TrackballControls.js'
import { STLLoader } from 'https://esm.sh/three@0.164.1/addons/loaders/STLLoader.js'
import URDFLoader from 'https://esm.sh/urdf-loader@0.12.1'

const scene = new THREE.Scene()
scene.background = new THREE.Color(0x263238)

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 10000)
camera.position.z = 100
camera.position.y = -400

const renderer = new THREE.WebGLRenderer({
  antialias: true
})
renderer.outputEncoding = THREE.sRGBEncoding
renderer.shadowMap.enabled = true
renderer.shadowMap.type = THREE.PCFSoftShadowMap
renderer.setSize(window.innerWidth, window.innerHeight)
document.body.appendChild(renderer.domElement)

const controls = new TrackballControls(camera, renderer.domElement)
controls.rotateSpeed = 5.0

const backLight = new THREE.DirectionalLight(0xffffff, 1.0)
backLight.position.set(0, 1000, 0)
scene.add(backLight)

const frontLight = new THREE.DirectionalLight(0xffffff, 1.0)
frontLight.position.set(0, -1000, 0)
scene.add(frontLight)

const ambientLight = new THREE.AmbientLight(0xffffff, 1)
scene.add(ambientLight)

const manager = new THREE.LoadingManager()
const loader = new URDFLoader(manager)

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(250, 128),
  new THREE.MeshPhysicalMaterial({
    opacity: 0.5,
    transparent: true,
    side: THREE.DoubleSide
  })
)
scene.add(ground)

const meshes = []

const stls = new Map()

const stl2mesh = (stl) => {
  const mesh = new THREE.Mesh(stl, new THREE.MeshPhongMaterial())
  meshes.push(mesh)
  return mesh
}

loader.loadMeshCb = (path, manager, onComplete) => {
  if (stls.has(path)) {
    const stl = stls.get(path)
    if (stl.geometry != null) {
      onComplete(stl2mesh(stl.geometry))
    } else {
      stl.onLoadCallbacks.push(onComplete)
    }
  } else {
    const stl = {
      geometry: null,
      onLoadCallbacks: [onComplete]
    }
    stls.set(path, stl)
    new STLLoader(manager).load(
      path,
      result => {
        for (const callback of stl.onLoadCallbacks) {
          callback(stl2mesh(result))
        }
      }
    )
  }
}

let robot = null

loader.load(
  'robot.urdf',
  r => {
    robot = r
    scene.add(robot)
  }
)

let angle = 0
const maxAngle = Math.PI / 2

document.body.addEventListener("keydown", (event) => {
  if (event.code === 'BracketLeft') {
    angle += 0.01;
  }
  if (event.code === 'BracketRight') {
    angle -= 0.01;
  }
})

const animate = () => {
  setTimeout(() => {
    requestAnimationFrame(animate)
  }, 1000 / 24)
  controls.update()
  renderer.render(scene, camera)
  if (robot != null) {
    for (let i = 0; i < 6; i++) {
      robot.setJointValue(`joint${i}a`, i % 2 === 0 ? angle : -angle)
    }
  }
}
animate()

document.addEventListener('mousedown', (event) => {
  event.preventDefault()
  const mouse3D = new THREE.Vector3(
    (event.clientX / window.innerWidth) * 2 - 1,
    -(event.clientY / window.innerHeight) * 2 + 1,
    0.5)
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(mouse3D, camera)
  const intersects = raycaster.intersectObjects(meshes)
  if (intersects.length > 0) {
    // intersects[0].object.material.color.setHex(Math.random() * 0xffffff)
  }
})

window.addEventListener('resize', () => {
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(window.devicePixelRatio)
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
})

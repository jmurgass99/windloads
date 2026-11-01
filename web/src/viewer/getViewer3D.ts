import * as THREE from "three";
import type { WindResult } from "../data-model.ts";

export function createWindViewer3D(container: HTMLElement): {
  update: (widthBM: number, depthDM: number, res: WindResult) => void;
} {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x070b14);

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 300);
  camera.position.set(36, 26, 38);
  camera.lookAt(0, 9, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  container.appendChild(renderer.domElement);

  const ambient = new THREE.AmbientLight(0xffffff, 0.72);
  const dir = new THREE.DirectionalLight(0xffffff, 0.9);
  dir.position.set(20, 40, 25);
  scene.add(ambient, dir);

  const group = new THREE.Group();
  scene.add(group);

  const resize = () => {
    const w = container.clientWidth || 640;
    const h = container.clientHeight || 480;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  };
  window.addEventListener("resize", resize);
  setTimeout(resize, 0);

  const animate = () => {
    requestAnimationFrame(animate);
    group.rotation.y += 0.002;
    renderer.render(scene, camera);
  };
  animate();

  return {
    update(widthBM: number, depthDM: number, res: WindResult) {
      while (group.children.length > 0) group.remove(group.children[0]);

      const qpMax = Math.max(res.qpTopKpa, 0.5);
      for (const p of res.panels) {
        if (p.zone === "D" || p.zone === "E") {
          const isWindward = p.zone === "D";
          const ratio = Math.min(1, p.qpKpa / qpMax);
          const color = new THREE.Color().setHSL(isWindward ? 0.04 + 0.08 * (1 - ratio) : 0.58, 0.85, 0.5);
          const geo = new THREE.BoxGeometry(widthBM * 0.98, p.heightM * 0.92, 0.35);
          const mat = new THREE.MeshStandardMaterial({ color, transparent: true, opacity: 0.82 });
          const mesh = new THREE.Mesh(geo, mat);
          mesh.position.set(0, p.zMidM, isWindward ? depthDM / 2 : -depthDM / 2);
          group.add(mesh);
        } else {
          // Zonas de cubierta F, G, H, I
          const zoneIdx = ["F", "G", "H", "I"].indexOf(p.zone);
          const geo = new THREE.BoxGeometry(widthBM * 0.96, 0.35, (depthDM / 4) * 0.92);
          const mat = new THREE.MeshStandardMaterial({
            color: zoneIdx <= 1 ? 0xef4444 : 0x38bdf8,
            transparent: true,
            opacity: 0.78,
          });
          const mesh = new THREE.Mesh(geo, mat);
          mesh.position.set(0, p.zMidM, depthDM / 2 - ((zoneIdx + 0.5) * depthDM) / 4);
          group.add(mesh);
        }
      }
    },
  };
}

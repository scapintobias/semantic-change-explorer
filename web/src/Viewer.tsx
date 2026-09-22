/**
 * Imperative Three scene lives behind a small React boundary; no global store.
 *
 * @format
 */

import { useEffect, useRef, useState } from 'react';
import * as T from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import type { Mode, Report } from './types';
import { opacities } from './semantics';

type Props = {
	report: Report;
	assetBase: string;
	selected: string;
	onSelect: (id: string) => void;
	mode: Mode;
	mix: number;
	changedOnly: boolean;
	fit: number;
	reset: number;
};
type State = {
	scene: T.Scene;
	camera: T.PerspectiveCamera;
	controls: OrbitControls;
	roots: T.Group[];
	meshes: T.Mesh[];
	box: T.Box3Helper;
	arrow: T.ArrowHelper;
	render: () => void;
	fit: (selected?: string) => void;
};
export function Viewer(props: Props) {
	const host = useRef<HTMLDivElement>(null);
	const engine = useRef<State | null>(null);
	const latest = useRef(props);
	latest.current = props;
	const [load, setLoad] = useState('Loading both scene states…');
	const [ready, setReady] = useState(false);
	useEffect(() => {
		const el = host.current!;
		let disposed = false;
		let renderer: T.WebGLRenderer;
		try {
			renderer = new T.WebGLRenderer({
				antialias: true,
				preserveDrawingBuffer: true,
			});
		} catch {
			setLoad(
				'WebGL is unavailable. The semantic index remains usable; enable hardware acceleration or use another browser.',
			);
			return;
		}
		renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
		renderer.setClearColor(0x161c23);
		el.appendChild(renderer.domElement);
		renderer.domElement.setAttribute(
			'aria-label',
			'3D comparison. Drag to orbit, scroll to zoom; select entities using the adjacent change index.',
		);
		const scene = new T.Scene();
		const camera = new T.PerspectiveCamera(38, 1, 0.01, 10000);
		const controls = new OrbitControls(camera, renderer.domElement);
		controls.enableDamping = false;
		scene.add(new T.HemisphereLight(0xd9eaff, 0x646568, 3));
		const light = new T.DirectionalLight(0xffffff, 4);
		light.position.set(5, 10, 7);
		scene.add(light);
		const grid = new T.GridHelper(24, 48, 0x394654, 0x25323d);
		grid.position.y = -0.4;
		scene.add(grid);
		const box = new T.Box3Helper(new T.Box3(), 0xf3d181);
		scene.add(box);
		box.visible = false;
		const arrow = new T.ArrowHelper(
			new T.Vector3(1, 0, 0),
			new T.Vector3(),
			1,
			0xf3d181,
		);
		scene.add(arrow);
		arrow.visible = false;
		const roots: T.Group[] = [],
			meshes: T.Mesh[] = [];
		const render = () => {
			if (!disposed) renderer.render(scene, camera);
		};
		const fit = (selected?: string) => {
			const bounds = new T.Box3();
			meshes
				.filter((m) => !selected || m.userData.record === selected)
				.forEach((m) => bounds.expandByObject(m));
			if (bounds.isEmpty()) return;
			const center = bounds.getCenter(new T.Vector3());
			const radius = Math.max(
				bounds.getSize(new T.Vector3()).length(),
				0.2,
			);
			camera.position
				.copy(center)
				.add(
					new T.Vector3(0.9, 0.8, 1.1)
						.normalize()
						.multiplyScalar(radius * 1.5),
				);
			camera.near = Math.max(radius / 1000, 0.001);
			camera.far = Math.max(radius * 100, 1000);
			camera.updateProjectionMatrix();
			controls.target.copy(center);
			controls.update();
			render();
		};
		engine.current = {
			scene,
			camera,
			controls,
			roots,
			meshes,
			box,
			arrow,
			render,
			fit,
		};
		const observer = new ResizeObserver(() => {
			const w = el.clientWidth,
				h = el.clientHeight;
			renderer.setSize(w, h);
			camera.aspect = w / h;
			camera.updateProjectionMatrix();
			render();
		});
		observer.observe(el);
		controls.addEventListener('change', render);
		let down = [0, 0];
		const pointerDown = (e: PointerEvent) => {
			down = [e.clientX, e.clientY];
		};
		const pointerUp = (e: PointerEvent) => {
			if (Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5)
				return;
			const rect = el.getBoundingClientRect();
			const ray = new T.Raycaster();
			ray.setFromCamera(
				new T.Vector2(
					((e.clientX - rect.left) / rect.width) * 2 - 1,
					(-(e.clientY - rect.top) / rect.height) * 2 + 1,
				),
				camera,
			);
			const hits = ray.intersectObjects(
				meshes.filter((m) => m.visible),
				false,
			);
			if (hits.length)
				latest.current.onSelect(hits[0].object.userData.record);
		};
		renderer.domElement.addEventListener('pointerdown', pointerDown);
		renderer.domElement.addEventListener('pointerup', pointerUp);
		const started = performance.now();
		const manager = new T.LoadingManager();
		manager.setURLModifier((url) => {
			const resolved = new URL(url, window.location.href);
			if (
				resolved.origin !== window.location.origin &&
				!url.startsWith('blob:') &&
				!url.startsWith('data:')
			)
				throw new Error('External model resource refused');
			return url;
		});
		const loader = new GLTFLoader(manager);
		Promise.all(
			['a.glb', 'b.glb'].map(async (file, side) => {
				const gltf = await loader.loadAsync(
					new URL(file, props.assetBase).toString(),
				);
				if (disposed) return;
				const root = gltf.scene;
				roots[side] = root;
				root.traverse((node) => {
					if (!(node instanceof T.Mesh)) return;
					let owner: T.Object3D | null = node;
					while (owner && !owner.userData.sce_entity)
						owner = owner.parent;
					const id = owner?.userData.sce_entity;
					const record = latest.current.report.diff.records.find(
						(r) => (side === 0 ? r.before : r.after) === id,
					);
					if (!record) {
						node.visible = false;
						return;
					}
					node.userData = {
						...node.userData,
						record: record.id,
						side,
						status: record.status,
					};
					const original = Array.isArray(node.material)
						? node.material
						: [node.material];
					const cloned = original.map((m) => {
						const clone = (m as T.MeshStandardMaterial).clone();
						clone.userData.base = clone.color.clone();
						clone.side = T.DoubleSide;
						return clone;
					});
					node.material = Array.isArray(node.material)
						? cloned
						: cloned[0];
					meshes.push(node);
				});
				scene.add(root);
			}),
		)
			.then(() => {
				if (disposed) return;
				fit();
				setLoad(
					`Both states loaded · ${((performance.now() - started) / 1000).toFixed(2)} s`,
				);
				setReady(true);
			})
			.catch((error) => {
				if (!disposed)
					setLoad(
						`Model loading failed: ${error.message}. Regenerate the report and check its GLB files.`,
					);
			});
		return () => {
			disposed = true;
			observer.disconnect();
			controls.dispose();
			scene.traverse((o) => {
				if (o instanceof T.Mesh) {
					o.geometry.dispose();
					(Array.isArray(o.material)
						? o.material
						: [o.material]
					).forEach((m) => m.dispose());
				}
			});
			renderer.dispose();
			renderer.domElement.remove();
			engine.current = null;
		};
	}, [props.report]);
	useEffect(() => {
		const s = engine.current;
		if (!s || !ready) return;
		const opacity = opacities(props.mode, props.mix);
		const bounds = new T.Box3();
		for (const mesh of s.meshes) {
			const side = mesh.userData.side as number,
				status = mesh.userData.status;
			const selected = mesh.userData.record === props.selected;
			mesh.visible =
				opacity[side] > 0.01 &&
				(!props.changedOnly || status !== 'unchanged');
			for (const mat of (Array.isArray(mesh.material)
				? mesh.material
				: [mesh.material]) as T.MeshStandardMaterial[]) {
				mat.opacity = opacity[side];
				mat.transparent = mat.opacity < 1;
				mat.depthWrite = mat.opacity > 0.6;
				mat.color.copy(mat.userData.base);
				if (status === 'removed') mat.color.set(0xe08c7f);
				if (status === 'added') mat.color.set(0x7ed1a3);
				if (status === 'ambiguous') mat.color.set(0xbdacf0);
				mat.emissive.set(selected ? 0x77602a : 0x000000);
				mat.emissiveIntensity = 0.38;
				mat.wireframe = side === 0 && props.mode === 'Overlay';
			}
			if (selected && mesh.visible) bounds.expandByObject(mesh);
		}
		s.box.box.copy(bounds);
		s.box.visible = !bounds.isEmpty();
		s.arrow.visible = false;
		const selected = props.report.diff.records.find(
			(r) => r.id === props.selected,
		);
		if (selected?.before && selected?.after) {
			const a = props.report.before.entities.find(
				(e) => e.id === selected.before,
			)?.extensions.blender?.evaluated_world;
			const b = props.report.after.entities.find(
				(e) => e.id === selected.after,
			)?.extensions.blender?.evaluated_world;
			if (a && b) {
				const from = new T.Vector3(a[0][3], a[2][3], -a[1][3]);
				const to = new T.Vector3(b[0][3], b[2][3], -b[1][3]);
				const delta = to.clone().sub(from);
				if (delta.length() > 1e-5) {
					s.arrow.position.copy(from);
					s.arrow.setDirection(delta.clone().normalize());
					s.arrow.setLength(delta.length(), 0.16, 0.08);
					s.arrow.visible = true;
				}
			}
		}
		s.render();
	}, [
		ready,
		props.selected,
		props.mode,
		props.mix,
		props.changedOnly,
		props.report,
	]);
	useEffect(() => {
		if (props.fit) engine.current?.fit(props.selected);
	}, [props.fit]);
	useEffect(() => {
		if (props.reset) engine.current?.fit();
	}, [props.reset]);
	return (
		<div className='viewport'>
			<div
				ref={host}
				className='canvas'
			/>
			<div className='view-label'>
				PERSPECTIVE <span> / </span> EVALUATED GEOMETRY
			</div>
			<div className='view-footer'>
				<span>
					Orbit · drag &nbsp; Pan · right drag &nbsp; Zoom · scroll
				</span>
				<span role='status'>{load}</span>
			</div>
		</div>
	);
}

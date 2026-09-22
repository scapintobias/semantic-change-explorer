/** @format */

import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Viewer } from './Viewer';
import {
	formatValue,
	nextRecord,
	symbols,
	visibleRecords,
	valueRows,
} from './semantics';
import type { Mode, Report } from './types';
import './style.css';

// The active comparison screen is defined below and is used for the final
// report view after a successful local comparison.

function ProcessingOverlay({
	progress,
	step,
}: {
	progress: number;
	step: string;
}) {
	return (
		<div className='overlay'>
			<div className='overlay-card'>
				<p className='eyebrow'>LOCAL PROCESSING</p>
				<h2>Comparing scene states…</h2>
				<p className='overlay-step'>{step}</p>
				<div
					className='progress-bar'
					aria-live='polite'>
					<div
						className='progress-fill'
						style={{ width: `${progress}%` }}
					/>
				</div>
				<div className='progress-meta'>Progress: {progress}%</div>
			</div>
		</div>
	);
}

function ComparisonApp({
	report,
	assetBase,
	onLoadNew,
}: {
	report: Report;
	assetBase: string;
	onLoadNew: () => void;
}) {
	const records = report.diff.records;
	const [selected, setSelected] = useState(
		records.find((r) => r.changes.some((c) => c.category === 'moved'))
			?.id ||
			records[0]?.id ||
			'',
	);
	const [mode, setMode] = useState<Mode>('Overlay');
	const [mix, setMix] = useState(0.5);
	const [changed, setChanged] = useState(false);
	const [category, setCategory] = useState('all');
	const [query, setQuery] = useState('');
	const [fit, setFit] = useState(0);
	const [reset, setReset] = useState(0);

	const filtered = visibleRecords(records, changed, category, query);
	const navigation = filtered.filter((r) => r.status !== 'unchanged');
	const record = records.find((r) => r.id === selected);
	const move = (direction: number) => {
		const id = nextRecord(navigation, selected, direction);
		if (id) setSelected(id);
	};

	useEffect(() => {
		const key = (event: KeyboardEvent) => {
			if ((event.target as HTMLElement).matches('input,select,textarea'))
				return;
			if (event.key === ']') {
				event.preventDefault();
				move(1);
			}
			if (event.key === '[') {
				event.preventDefault();
				move(-1);
			}
			if (event.key.toLowerCase() === 'f') setFit((v) => v + 1);
		};
		window.addEventListener('keydown', key);
		return () => window.removeEventListener('keydown', key);
	}, [selected, navigation]);

	const selectedEntity =
		report.after.entities.find((e) => e.id === record?.after) ||
		report.before.entities.find((e) => e.id === record?.before);
	const sourceEntities = record?.after
		? report.after.entities
		: report.before.entities;
	const candidates = report.diff.ambiguity.filter(
		(c) => c.before === record?.before || c.after === record?.after,
	);

	return (
		<div className='app'>
			<header>
				<div className='brand'>
					<span className='brandmark'>◈</span>
					<div>
						SEMANTIC CHANGE EXPLORER
						<small>LOCAL COMPARISON · v1.0.0</small>
					</div>
				</div>
				<div className='sources'>
					<span>A</span> {report.before.source.name} <b>→</b>{' '}
					<span>B</span> {report.after.source.name}
				</div>
				<button
					className='secondary'
					onClick={onLoadNew}>
					Load new files
				</button>
			</header>
			<div className='summary'>
				<strong>Understand the difference.</strong>
				<div>
					{Object.entries(report.diff.summary).map(([s, n]) => (
						<span
							key={s}
							className={s}>
							{symbols[s]} {n} {s}
						</span>
					))}
				</div>
			</div>
			<main>
				<aside className='index'>
					<div className='section-title'>
						CHANGE INDEX <span>{filtered.length} entities</span>
					</div>
					<input
						aria-label='Find entity'
						placeholder='Find an entity…'
						value={query}
						onChange={(e) => setQuery(e.target.value)}
					/>
					<div className='filters'>
						<label>
							<input
								type='checkbox'
								checked={changed}
								onChange={(e) => setChanged(e.target.checked)}
							/>{' '}
							Changed only
						</label>
						<select
							aria-label='Change category'
							value={category}
							onChange={(e) => setCategory(e.target.value)}>
							<option value='all'>All categories</option>
							{[
								'added',
								'removed',
								'ambiguous',
								'moved',
								'geometry',
								'topology',
								'modifier',
								'material',
								'relationship',
								'evaluated',
							].map((c) => (
								<option key={c}>{c}</option>
							))}
						</select>
					</div>
					<nav aria-label='Entities'>
						{filtered.map((r) => (
							<button
								key={r.id}
								aria-pressed={selected === r.id}
								onClick={() => setSelected(r.id)}
								className={
									'entity ' +
									(selected === r.id ? 'selected' : '')
								}>
								<span className={'symbol ' + r.status}>
									{symbols[r.status]}
								</span>
								<span>
									<strong>{r.name}</strong>
									<small>
										{r.type.replace('blender.', '')} ·{' '}
										{r.status}
									</small>
								</span>
							</button>
						))}
						{!filtered.length && (
							<p className='empty'>
								No entities match these filters.
							</p>
						)}
					</nav>
					<div className='navigation'>
						<button
							onClick={() => move(-1)}
							disabled={!navigation.length}>
							← Previous [
						</button>
						<button
							onClick={() => move(1)}
							disabled={!navigation.length}>
							Next ] →
						</button>
					</div>
				</aside>

				<section className='spatial'>
					<div className='toolbar'>
						<div className='modes'>
							{(['A', 'B', 'Overlay', 'Compare'] as Mode[]).map(
								(m) => (
									<button
										key={m}
										aria-pressed={mode === m}
										onClick={() => setMode(m)}>
										{m === 'A'
											? 'A only'
											: m === 'B'
												? 'B only'
												: m}
									</button>
								),
							)}
						</div>
						<div>
							<button onClick={() => setFit((v) => v + 1)}>
								Fit selected · F
							</button>
							<button onClick={() => setReset((v) => v + 1)}>
								Fit scene
							</button>
						</div>
					</div>
					<Viewer
						report={report}
						assetBase={assetBase}
						selected={selected}
						onSelect={setSelected}
						mode={mode}
						mix={mix}
						changedOnly={changed}
						fit={fit}
						reset={reset}
					/>
					<div className='comparison'>
						<span>A / BEFORE</span>
						<input
							aria-label='A to B comparison'
							type='range'
							min='0'
							max='1'
							step='0.01'
							value={mix}
							onChange={(e) => {
								setMix(Number(e.target.value));
								setMode('Compare');
							}}
						/>
						<span>B / AFTER</span>
					</div>
					<div className='legend'>
						<span>− A: wireframe ghost</span>
						<span>+ B: solid geometry</span>
						<span>↗ Arrow: world-position delta</span>
						<span>? Correspondence unresolved</span>
					</div>
					<p className='note'>
						Crossfade compares two states; it is not an animation or
						a topology morph. Solid colors simplify source
						materials.
					</p>
				</section>

				<aside className='inspector'>
					<div className='section-title'>SEMANTIC INSPECTOR</div>
					{record && (
						<>
							<div className='selection-head'>
								<span className={'tag ' + record.status}>
									{symbols[record.status]} {record.status}
								</span>
								<h1>{record.name}</h1>
								<p>{record.type}</p>
							</div>
							<div className='confidence'>
								<strong>{record.match.confidence}</strong>
								<p>
									{record.match.evidence.join(' · ') ||
										(record.status === 'ambiguous'
											? 'Multiple candidates remain plausible. No correspondence has been forced.'
											: 'No supported correspondence found. Addition/removal is relative to this matcher.')}
								</p>
							</div>
							<dl className='relationships'>
								{Object.entries(
									selectedEntity?.relations || {},
								).map(([key, ids]) => (
									<div key={key}>
										<dt>{key}</dt>
										<dd>
											{ids
												.map(
													(id) =>
														sourceEntities.find(
															(e) => e.id === id,
														)?.name || id,
												)
												.join(', ') || '—'}
										</dd>
									</div>
								))}
							</dl>
							{candidates.map((c, i) => (
								<div
									className='candidate'
									key={i}>
									?{' '}
									{
										report.before.entities.find(
											(e) => e.id === c.before,
										)?.name
									}{' '}
									↔{' '}
									{
										report.after.entities.find(
											(e) => e.id === c.after,
										)?.name
									}
									<small>{c.evidence.join(' · ')}</small>
								</div>
							))}
							{['authored', 'evaluated'].map((domain) => (
								<section
									key={domain}
									className='change-section'>
									<h2>
										{domain === 'authored'
											? 'Authored state'
											: 'Evaluated outcome'}
									</h2>
									{record.changes
										.filter((c) => c.domain === domain)
										.map((c, i) => (
											<article
												className='change'
												key={i}>
												<h3>{c.label}</h3>
												<div className='values'>
													{valueRows(
														c.before,
														c.after,
													).map((row, j) => (
														<div
															className='field-delta'
															key={j}>
															{row.path && (
																<small>
																	{row.path}
																</small>
															)}
															<div>
																<b>A</b>
																<span>
																	{formatValue(
																		row.before,
																	)}
																</span>
															</div>
															<div>
																<b>B</b>
																<span>
																	{formatValue(
																		row.after,
																	)}
																</span>
															</div>
														</div>
													))}
												</div>
												{c.displacement && (
													<p>
														{
															c.displacement
																.changed_vertices
														}{' '}
														vertices displaced · max{' '}
														{formatValue(
															c.displacement.max,
														)}{' '}
														local units
													</p>
												)}
												{c.compatible === false && (
													<p>
														Topology incompatible.
														Before/after overlay
														only.
													</p>
												)}
											</article>
										))}
									{!record.changes.some(
										(c) => c.domain === domain,
									) && (
										<p className='muted'>
											{record.status === 'unchanged' ||
											record.status === 'modified'
												? 'No difference detected in compared fields.'
												: 'No matched pair to compare.'}
										</p>
									)}
								</section>
							))}
						</>
					)}
					<details className='coverage'>
						<summary>Coverage & interpretation limits</summary>
						<p>
							Derived differences are observations, not proof of
							which authored edit caused them.
						</p>
						<ul>
							{report.diff.coverage.not_compared.map((c) => (
								<li key={c}>{c}</li>
							))}
						</ul>
						<p>
							One saved frame and active view layer. No persistent
							identity guarantee. Numeric tolerance: 0.00001
							native units.
						</p>
						<details>
							<summary>Extraction contexts</summary>
							<p>{formatValue(report.diff.context)}</p>
						</details>
					</details>
				</aside>
			</main>
			<footer>
				<span>Authored intent → evaluated outcome</span>
				<span>
					No files leave your computer. Selected files are transferred
					only to the local loopback service, processed locally in a
					temporary workspace, and removed after processing.
				</span>
				<span>INDEX [ ] &nbsp; FIT F</span>
			</footer>
		</div>
	);
}

function ReadyWorkspace({
	processing,
	progress,
	step,
	onCompare,
}: {
	processing: boolean;
	progress: number;
	step: string;
	onCompare: (before: File, after: File) => Promise<void>;
}) {
	const [before, setBefore] = useState<File | null>(null);
	const [after, setAfter] = useState<File | null>(null);
	const [error, setError] = useState('');
	const [busy, setBusy] = useState(false);

	const submit = async () => {
		if (!before || !after) {
			setError('Select both a Before and After .blend file.');
			return;
		}
		setBusy(true);
		setError('');
		try {
			await onCompare(before, after);
		} catch (exc) {
			setError(
				exc instanceof Error
					? exc.message
					: 'Unknown comparison error.',
			);
			setBusy(false);
		}
	};

	return (
		<div className='app app-ready'>
			<header>
				<div className='brand'>
					<span className='brandmark'>◈</span>
					<div>
						SEMANTIC CHANGE EXPLORER
						<small>LOCAL COMPARISON · v1.0.0</small>
					</div>
				</div>
				<div className='sources'>
					<span>A</span> BEFORE <b>→</b> <span>B</span> AFTER
				</div>
			</header>
			<div className='summary'>
				<strong>Understand the difference.</strong>
				<div>
					<span className='added'>• added</span>
					<span className='removed'>• removed</span>
					<span className='modified'>• modified</span>
				</div>
			</div>
			<main>
				<aside className='index'>
					<div className='section-title'>
						CHANGE INDEX <span>waiting</span>
					</div>
					<div className='placeholder'>
						Choose the Before and After files to populate the
						comparison index.
					</div>
				</aside>
				<section className='spatial'>
					<div className='toolbar'>
						<div className='modes'>
							<button aria-pressed='true'>Overlay</button>
							<button>A only</button>
							<button>B only</button>
						</div>
						<div>
							<button>Fit selected · F</button>
							<button>Fit scene</button>
						</div>
					</div>
					<div className='empty-viewport'>
						<div className='empty-viewport-copy'>
							<p>Waiting for two scenes</p>
							<small>
								Load a Before and After .blend to begin.
							</small>
						</div>
					</div>
				</section>
				<aside className='inspector'>
					<div className='section-title'>SEMANTIC INSPECTOR</div>
					<div className='placeholder'>
						The scene diff will open here once the comparison has
						finished.
					</div>
				</aside>
			</main>
			<footer>
				<span>Local-only workflow</span>
				<span>Loopback service only</span>
				<span>Temporary workspace</span>
			</footer>
			{processing ? (
				<ProcessingOverlay
					progress={progress}
					step={step}
				/>
			) : (
				<div className='overlay'>
					<div className='overlay-card'>
						<p className='eyebrow'>ADD BEFORE / AFTER</p>
						<h2>Select the two .blend files</h2>
						<div className='upload-grid'>
							<label className='dropzone'>
								<span>Before</span>
								<input
									type='file'
									accept='.blend'
									onChange={(e) =>
										setBefore(e.target.files?.[0] ?? null)
									}
								/>
								<strong>
									{before
										? before.name
										: 'Choose Before .blend'}
								</strong>
							</label>
							<label className='dropzone'>
								<span>After</span>
								<input
									type='file'
									accept='.blend'
									onChange={(e) =>
										setAfter(e.target.files?.[0] ?? null)
									}
								/>
								<strong>
									{after ? after.name : 'Choose After .blend'}
								</strong>
							</label>
						</div>
						<div className='overlay-actions'>
							<button
								className='swap'
								type='button'
								onClick={() => {
									const nextBefore = after;
									setAfter(before);
									setBefore(nextBefore);
								}}>
								Swap
							</button>
							<button
								className='primary'
								type='button'
								disabled={busy || !before || !after}
								onClick={() => {
									void submit();
								}}>
								{busy ? 'Comparing…' : 'Compare'}
							</button>
						</div>
						{error && <p className='error-text'>{error}</p>}
					</div>
				</div>
			)}
		</div>
	);
}

function App() {
	const [report, setReport] = useState<Report | null>(null);
	const [assetBase, setAssetBase] = useState(
		new URL('./', window.location.href).toString(),
	);
	const [loading, setLoading] = useState(true);
	const [processing, setProcessing] = useState(false);
	const [progress, setProgress] = useState(0);
	const [step, setStep] = useState('Preparing local comparison');

	useEffect(() => {
		fetch('./report.json', { cache: 'no-store' })
			.then((response) => {
				if (!response.ok) return null;
				return response.json();
			})
			.then((payload) => {
				if (payload && payload.diff?.summary) {
					setReport(payload);
					setAssetBase(
						new URL('./', window.location.href).toString(),
					);
				}
			})
			.finally(() => setLoading(false));
	}, []);

	const loadNew = () => {
		setReport(null);
		setAssetBase(new URL('./', window.location.href).toString());
		setProcessing(false);
		setProgress(0);
		setStep('Preparing local comparison');
	};

	const handleCompare = async (before: File, after: File) => {
		const form = new FormData();
		form.append('before', before, before.name);
		form.append('after', after, after.name);

		const response = await fetch('/api/compare', {
			method: 'POST',
			body: form,
		});
		const payload = await response.json();
		if (!response.ok || !payload.ok) {
			throw new Error(payload.error || 'The local comparison failed.');
		}

		setProcessing(true);
		setProgress(0);
		setStep('Sending files to the local loopback service');

		const jobBase = payload.job_url.endsWith('/')
			? payload.job_url
			: `${payload.job_url}/`;
		const statusUrl = new URL('status.json', jobBase);

		const poll = async (): Promise<void> => {
			const statusResponse = await fetch(statusUrl, {
				cache: 'no-store',
			});
			if (!statusResponse.ok) {
				setProcessing(false);
				throw new Error('The comparison status could not be read.');
			}

			const status = await statusResponse.json();
			const nextProgress = Number(status.progress ?? 0);
			setProgress(
				Number.isFinite(nextProgress)
					? Math.min(100, Math.max(0, nextProgress))
					: 0,
			);
			setStep(status.step || 'Processing local scene');

			if (status.state === 'complete') {
				const reportResponse = await fetch(
					new URL('report.json', jobBase),
					{
						cache: 'no-store',
					},
				);
				if (!reportResponse.ok) {
					setProcessing(false);
					throw new Error(
						'The comparison completed but the report was not ready.',
					);
				}
				const nextReport = await reportResponse.json();
				if (nextReport && nextReport.diff?.summary) {
					setReport(nextReport);
					setAssetBase(jobBase);
					setProcessing(false);
					return;
				}
				setProcessing(false);
				throw new Error(
					'The comparison completed but the report was malformed.',
				);
			}

			if (status.state === 'error') {
				setProcessing(false);
				throw new Error(status.error || 'The comparison failed.');
			}

			await new Promise((resolve) => setTimeout(resolve, 800));
			return poll();
		};

		await poll();
	};

	if (loading) {
		return <div className='loading'>Loading local application…</div>;
	}

	if (report) {
		return (
			<ComparisonApp
				report={report}
				assetBase={assetBase}
				onLoadNew={loadNew}
			/>
		);
	}

	return (
		<ReadyWorkspace
			processing={processing}
			progress={progress}
			step={step}
			onCompare={handleCompare}
		/>
	);
}

const root = createRoot(document.getElementById('root')!);
root.render(<App />);

const BLOB_CLASSES = [
  'gradient-blob gradient-blob-1',
  'gradient-blob gradient-blob-2',
  'gradient-blob gradient-blob-3',
  'gradient-blob gradient-blob-4',
]

export function GradientMesh({
  blobOpacities = [1, 1, 1, 1],
  noise = true,
}: {
  blobOpacities?: number[]
  noise?: boolean
}) {
  return (
    <>
      <div className="gradient-mesh">
        {blobOpacities.map((opacity, i) => (
          <div
            key={i}
            className={BLOB_CLASSES[i]}
            style={opacity < 1 ? { opacity } : undefined}
          />
        ))}
      </div>
      {noise && <div className="noise-overlay" />}
    </>
  )
}

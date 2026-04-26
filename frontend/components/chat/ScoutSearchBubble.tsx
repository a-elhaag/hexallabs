'use client'
import { useState } from 'react'
import { Globe, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'

export interface ScoutResult {
  query?: string
  summary: string
  urls: string[]
  result_count: number
  error?: string
  pending?: boolean
}

function FaviconOrGlobe({ url }: { url: string }) {
  const [failed, setFailed] = useState(false)
  try {
    const { origin } = new URL(url)
    if (!failed) {
      return (
        <img
          src={`${origin}/favicon.ico`}
          className="w-3.5 h-3.5 rounded-sm object-contain"
          onError={() => setFailed(true)}
          alt=""
        />
      )
    }
  } catch {}
  return <Globe className="w-3.5 h-3.5 text-warm-gray/60 shrink-0" />
}

function hostname(url: string) {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return url }
}

export function ScoutSearchBubble({ result }: { result: ScoutResult }) {
  const [open, setOpen] = useState(false)

  return (
    <div
      className="mx-auto w-full max-w-4xl px-6 py-1"
      style={{ animation: 'msgIn 0.28s cubic-bezier(0.16,1,0.3,1) both' }}
    >
      <div className="inline-flex flex-col border border-warm-gray/20 rounded-2xl bg-cream/60 backdrop-blur-sm overflow-hidden text-xs max-w-sm">
        {/* Header row */}
        <button
          onClick={() => setOpen(o => !o)}
          className="flex items-center gap-2 px-3 py-2.5 hover:bg-warm-gray/8 transition-colors text-left w-full"
        >
          <Globe className="w-3.5 h-3.5 text-denim shrink-0" />
          <span className="font-semibold text-[#2c2c2c] flex-1">
            {result.pending ? 'Searching the web…' : 'Searched the web'}
          </span>
          {!result.pending && (
            <>
              <span className="text-warm-gray/60 font-medium">
                {result.result_count} result{result.result_count !== 1 ? 's' : ''}
              </span>
              {open
                ? <ChevronUp className="w-3 h-3 text-warm-gray/60 shrink-0" />
                : <ChevronDown className="w-3 h-3 text-warm-gray/60 shrink-0" />
              }
            </>
          )}
          {result.pending && (
            <span className="w-3.5 h-3.5 border border-warm-gray/30 border-t-denim rounded-full animate-spin shrink-0" />
          )}
        </button>

        {/* Expanded URL list */}
        {open && !result.pending && (
          <div
            className="border-t border-warm-gray/15 flex flex-col"
            style={{ animation: 'expandDown 0.2s cubic-bezier(0.16,1,0.3,1) both' }}
          >
            {result.error ? (
              <p className="px-3 py-2 text-red-500/80">{result.error}</p>
            ) : (
              result.urls.slice(0, 8).map((url, i) => (
                <a
                  key={i}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-3 py-1.5 hover:bg-warm-gray/8 transition-colors group border-b border-warm-gray/10 last:border-b-0"
                >
                  <FaviconOrGlobe url={url} />
                  <span className="flex-1 truncate text-[#2c2c2c]/80 group-hover:text-[#2c2c2c]">
                    {hostname(url)}
                  </span>
                  <ExternalLink className="w-2.5 h-2.5 text-warm-gray/40 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                </a>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

"use client";

import { useVirtualizer } from "@tanstack/react-virtual";
import {
    ColumnDef,
    flexRender,
    getCoreRowModel,
    useReactTable,
} from "@tanstack/react-table";
import { useRef, useMemo, useState } from "react";
import { AuditEvent } from "@/lib/data/schemas";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { cn } from "@/lib/cn";
import { CheckCircle2, FileJson, ShieldAlert } from "lucide-react";
import { ProofDrawer } from "./ProofDrawer";

interface AuditTableProps {
    data: AuditEvent[];
    total: number;
    onFetchMore: () => void;
    isLoading: boolean;
}

export function AuditTable({ data, onFetchMore, isLoading }: AuditTableProps) {
    const parentRef = useRef<HTMLDivElement>(null);
    const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

    const columns = useMemo<ColumnDef<AuditEvent>[]>(() => [
        {
            accessorKey: "timestamp",
            header: "Timestamp",
            cell: (info) => (
                <span className="font-mono text-xs text-[var(--text-secondary)]">
                    {new Date(info.getValue<number>() * 1000).toISOString()}
                </span>
            ),
            size: 180,
        },
        {
            accessorKey: "event_type",
            header: "Type",
            cell: (info) => (
                <span className="px-1.5 py-0.5 rounded bg-[var(--glass-border)] text-[var(--text-secondary)] text-[10px] uppercase font-mono tracking-wider">
                    {info.getValue<string>()}
                </span>
            ),
            size: 140,
        },
        {
            accessorKey: "outcome",
            header: "Outcome",
            cell: (info) => {
                const val = info.getValue<string>();
                const colors = {
                    OK: "text-emerald-500",
                    DENY: "text-amber-500",
                    ERROR: "text-red-500"
                };
                return <span className={cn("font-bold text-xs", colors[val as keyof typeof colors])}>{val}</span>;
            },
            size: 80,
        },
        {
            accessorKey: "denial_reason",
            header: "Reason",
            cell: (info) => {
                const val = info.getValue<string>();
                if (!val) return <span className="text-[var(--text-muted)]">-</span>;
                return <span className="text-amber-500/80 text-[10px] font-mono">{val}</span>;
            },
            size: 150,
        },
        {
            id: "identity",
            header: "Identity",
            cell: (info) => {
                const { agent_id, peer_id } = info.row.original;
                return (
                    <div className="flex flex-col text-xs font-mono">
                        <span className="text-[var(--text-primary)]" title={agent_id}>A: {agent_id ? agent_id.slice(0, 8) : "?"}</span>
                        <span className="text-[var(--text-muted)]" title={peer_id}>P: {peer_id ? peer_id.slice(0, 8) : "?"}</span>
                    </div>
                )
            },
            size: 150,
        },
        {
            id: "proof",
            header: "Proof",
            cell: (info) => {
                const integrity = info.row.original.integrity;
                const valid = integrity.proof_state === "VERIFIED";
                return (
                    <div className="flex items-center gap-1.5">
                        {valid ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500/50" />
                        ) : (
                            <ShieldAlert className="w-3.5 h-3.5 text-amber-500/50" />
                        )}
                        <span className={cn("text-[10px]", valid ? "text-[var(--text-muted)]" : "text-amber-500")}>
                            {integrity.proof_state}
                        </span>
                    </div>
                )
            },
            size: 120,
        },
        {
            id: "actions",
            header: "",
            cell: (info) => (
                <button
                    onClick={(e) => { e.stopPropagation(); setSelectedEvent(info.row.original); }}
                    className="p-1 hover:bg-white/10 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                    title="View Proof & Evidence"
                >
                    <FileJson className="w-4 h-4" />
                </button>
            ),
            size: 50,
        }
    ], []);

    // eslint-disable-next-line react-hooks/incompatible-library
    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
    });

    const { rows } = table.getRowModel();

    const rowVirtualizer = useVirtualizer({
        count: rows.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 48, // 48px row height
        overscan: 10,
    });

    return (
        <>
            <GlassPanel className="w-full flex flex-col h-[calc(100vh-200px)] overflow-hidden">
                {/* Header */}
                <div className="flex items-center bg-[var(--panel)] border-b border-[var(--glass-border)] h-10 px-4">
                    {table.getHeaderGroups().map(headerGroup => (
                        <div key={headerGroup.id} className="flex flex-1 w-full">
                            {headerGroup.headers.map(header => (
                                <div
                                    key={header.id}
                                    style={{ width: header.getSize() }}
                                    className="text-[10px] uppercase font-bold text-[var(--text-muted)] tracking-wider flex-shrink-0"
                                >
                                    {flexRender(header.column.columnDef.header, header.getContext())}
                                </div>
                            ))}
                        </div>
                    ))}
                    {/* Scrollbar spacer */}
                    <div className="w-2" />
                </div>

                {/* Virtualized Body */}
                <div
                    ref={parentRef}
                    className="flex-1 overflow-auto"
                    onScroll={(e) => {
                        const target = e.target as HTMLDivElement;
                        if (target.scrollHeight - target.scrollTop - target.clientHeight < 200) {
                            if (!isLoading) onFetchMore();
                        }
                    }}
                >
                    <div
                        style={{
                            height: `${rowVirtualizer.getTotalSize()}px`,
                            width: '100%',
                            position: 'relative',
                        }}
                    >
                        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                            const row = rows[virtualRow.index];
                            return (
                                <div
                                    key={row.id}
                                    onClick={() => setSelectedEvent(row.original)}
                                    data-index={virtualRow.index}
                                    ref={rowVirtualizer.measureElement}
                                    className={cn(
                                        "absolute top-0 left-0 w-full flex items-center px-4 h-12 border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors group",
                                        virtualRow.index % 2 === 1 && "bg-white/[0.02]"
                                    )}
                                    style={{
                                        transform: `translateY(${virtualRow.start}px)`,
                                    }}
                                >
                                    {row.getVisibleCells().map(cell => (
                                        <div
                                            key={cell.id}
                                            style={{ width: cell.column.getSize() }}
                                            className="flex-shrink-0 overflow-hidden"
                                        >
                                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                        </div>
                                    ))}
                                </div>
                            );
                        })}
                    </div>
                    {isLoading && (
                        <div className="p-4 text-center text-xs text-[var(--text-muted)]">Loading more events...</div>
                    )}
                </div>
            </GlassPanel>

            {/* Proof Drawer */}
            {selectedEvent && (
                <>
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity" onClick={() => setSelectedEvent(null)} />
                    <ProofDrawer event={selectedEvent} onClose={() => setSelectedEvent(null)} />
                </>
            )}
        </>
    );
}

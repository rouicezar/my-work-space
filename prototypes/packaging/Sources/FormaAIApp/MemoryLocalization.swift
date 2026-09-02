import LifecycleContract

enum MemoryCopyKey {
    case memoryTitle, memorySyntheticOnly, memoryPreviewBadge
    case authorityBoundary, authorityBoundaryBody
    case claimKey, version, previousRecord, correlation
    case sources, firstRecorded, lastUpdated
    case provenance, reviewAction
}

extension ProductCopy {
    subscript(key: MemoryCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .memoryTitle): "受治理记忆"
        case (.simplifiedChinese, .memorySyntheticOnly): "5 个合成样例，用于检查最终产品如何呈现候选、确认、冲突、修正与删除。"
        case (.simplifiedChinese, .memoryPreviewBadge): "预览样例"
        case (.simplifiedChinese, .authorityBoundary): "记忆权威边界"
        case (.simplifiedChinese, .authorityBoundaryBody):
            "这里没有读取真实记忆，也没有连接 Semantica。正式产品只有在候选被批准并由 "
            + "Semantica 存储后才成为权威记录；任何提升、修正或删除都需来源、版本与审计证据，"
            + "且不在此预览中执行。"
        case (.simplifiedChinese, .claimKey): "主张键"
        case (.simplifiedChinese, .version): "版本"
        case (.simplifiedChinese, .previousRecord): "上一记录"
        case (.simplifiedChinese, .correlation): "关联 ID"
        case (.simplifiedChinese, .sources): "来源"
        case (.simplifiedChinese, .firstRecorded): "首次记录"
        case (.simplifiedChinese, .lastUpdated): "最近更新"
        case (.simplifiedChinese, .provenance): "来源与版本"
        case (.simplifiedChinese, .reviewAction): "仅查看 · 展示下一状态，绝不执行"
        case (.english, .memoryTitle): "Governed memory"
        case (.english, .memorySyntheticOnly): "Five synthetic examples for reviewing how the finished product presents candidate, confirmed, conflict, correction, and delete states."
        case (.english, .memoryPreviewBadge): "PREVIEW EXAMPLE"
        case (.english, .authorityBoundary): "Memory authority boundary"
        case (.english, .authorityBoundaryBody):
            "No real memory is read and no Semantica is connected here. In the "
            + "finished product, only approved candidates stored by Semantica "
            + "become authoritative. Any promote, correction, or delete requires "
            + "source, version, and audit evidence, and none is executed here."
        case (.english, .claimKey): "Claim key"
        case (.english, .version): "Version"
        case (.english, .previousRecord): "Previous record"
        case (.english, .correlation): "Correlation ID"
        case (.english, .sources): "Sources"
        case (.english, .firstRecorded): "First recorded"
        case (.english, .lastUpdated): "Last updated"
        case (.english, .provenance): "Provenance and version"
        case (.english, .reviewAction): "View only · show next state, never execute"
        }
    }

    func memoryStateTitle(_ state: GovernedMemoryReviewState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .candidate): "候选"
        case (.simplifiedChinese, .confirmed): "已确认"
        case (.simplifiedChinese, .conflict): "冲突"
        case (.simplifiedChinese, .correction): "修正"
        case (.simplifiedChinese, .deleted): "已删除"
        case (.english, .candidate): "Candidate"
        case (.english, .confirmed): "Confirmed"
        case (.english, .conflict): "Conflict"
        case (.english, .correction): "Correction"
        case (.english, .deleted): "Deleted"
        }
    }

    func memoryRecordTitle(_ state: GovernedMemoryReviewState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .candidate): "等待审核的候选事实"
        case (.simplifiedChinese, .confirmed): "Semantica 已确认的记忆"
        case (.simplifiedChinese, .conflict): "与已确认主张冲突"
        case (.simplifiedChinese, .correction): "对已确认记录的修正"
        case (.simplifiedChinese, .deleted): "已删除的记录（墓碑）"
        case (.english, .candidate): "Candidate fact awaiting review"
        case (.english, .confirmed): "Semantica-confirmed memory"
        case (.english, .conflict): "Conflicts with a confirmed claim"
        case (.english, .correction): "Correction to a confirmed record"
        case (.english, .deleted): "Deleted record (tombstone)"
        }
    }

    func memoryReason(_ state: GovernedMemoryReviewState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .candidate): "一个候选事实已有来源与关联 ID，但在被批准并由 Semantica 存储前不具权威性。"
        case (.simplifiedChinese, .confirmed): "记录已由 Semantica 存储并带版本；它是唯一权威，必须携带来源与关联 ID。"
        case (.simplifiedChinese, .conflict): "该候选与一条已确认主张文本等价但来源不同；在解决前不能发布为权威。"
        case (.simplifiedChinese, .correction): "确认记录被修正：旧版本作废并被新版本取代，二者均带版本与上一记录 ID。"
        case (.simplifiedChinese, .deleted): "记录已删除；其内容被移除，仅保留来源与审计轨迹作为墓碑，不提供静默恢复。"
        case (.english, .candidate): "A candidate has sources and a correlation ID, but is not authoritative until approved and stored by Semantica."
        case (.english, .confirmed): "The record is stored by Semantica and versioned; it is the sole authority and must carry sources and a correlation ID."
        case (.english, .conflict): "The candidate is text-normalized-equivalent to a confirmed claim but from different sources; it cannot become authoritative until resolved."
        case (.english, .correction): "A confirmed record is corrected: the previous version is superseded and replaced by a new version, both carrying version and previous-record IDs."
        case (.english, .deleted): "The record is deleted; its content is removed and only sources and audit trail remain as a tombstone, with no silent restore."
        }
    }

    func memoryProvenance(_ state: GovernedMemoryReviewState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .candidate): "来源 1 · 关联已绑定 · 未存储"
        case (.simplifiedChinese, .confirmed): "版本 1 · 来源已绑定 · 已由 Semantica 存储"
        case (.simplifiedChinese, .conflict): "与已确认主张冲突 · 需人工解决"
        case (.simplifiedChinese, .correction): "版本 2 · 替代版本 1"
        case (.simplifiedChinese, .deleted): "内容已移除 · 审计轨迹保留"
        case (.english, .candidate): "1 source · correlation bound · not stored"
        case (.english, .confirmed): "Version 1 · sources bound · stored by Semantica"
        case (.english, .conflict): "Conflicts with a confirmed claim · resolution needed"
        case (.english, .correction): "Version 2 · supersedes version 1"
        case (.english, .deleted): "Content removed · audit trail retained"
        }
    }
}

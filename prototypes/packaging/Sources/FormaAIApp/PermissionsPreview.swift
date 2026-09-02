import SwiftUI
import LifecycleContract

struct PermissionsPreview: View {
    let language: ProductLanguage
    @Binding var selection: PermissionScope

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        HStack(spacing: 0) {
            scopeList
            Divider()
            scopeDetail
        }
    }

    private var scopeList: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 5) {
                Text(copy[.permissionsTitle]).font(.title2.weight(.semibold))
                Text(copy[.permissionsSyntheticOnly]).font(.caption).foregroundStyle(.secondary)
            }
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(PermissionsContract.productDefault.scopes) { scope in
                        Button {
                            selection = scope
                        } label: {
                            HStack(alignment: .top, spacing: 10) {
                                Image(systemName: symbol(for: scope))
                                    .foregroundStyle(tint(for: scope)).frame(width: 18)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(copy.permissionScopeTitle(scope)).font(.callout.weight(.semibold))
                                    Text(scopeLabel(scope)).font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer(minLength: 0)
                            }
                            .padding(11).contentShape(Rectangle())
                            .background(selection == scope ? Color.accentColor.opacity(0.14) : Color.secondary.opacity(0.055), in: RoundedRectangle(cornerRadius: 11))
                            .overlay(RoundedRectangle(cornerRadius: 11).stroke(selection == scope ? Color.accentColor.opacity(0.55) : Color.clear))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .padding(20).frame(width: 250).background(.thinMaterial)
    }

    private var scopeDetail: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .top, spacing: 14) {
                    Image(systemName: symbol(for: selection))
                        .font(.title2).foregroundStyle(tint(for: selection))
                        .frame(width: 42, height: 42).background(tint(for: selection).opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                    VStack(alignment: .leading, spacing: 5) {
                        Text(copy.permissionScopeTitle(selection)).font(.title2.weight(.semibold))
                        Text(scopeLabel(selection)).font(.callout.weight(.semibold)).foregroundStyle(tint(for: selection))
                    }
                    Spacer()
                    Text(copy[.permissionsPreviewBadge]).font(.caption2.monospaced().weight(.bold))
                        .padding(.horizontal, 8).padding(.vertical, 5)
                        .background(Color.blue.opacity(0.12), in: Capsule()).foregroundStyle(.blue)
                }

                detailCard(copy.permissionScopeTitle(selection), copy.permissionScopeDetail(selection), "info.circle")

                VStack(alignment: .leading, spacing: 12) {
                    Label(copy[.approvalPolicy], systemImage: "hand.raised").font(.headline)
                    Text(copy[.permissionsAuthorityBoundaryBody]).font(.callout).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .cardStyle()

                VStack(alignment: .leading, spacing: 12) {
                    Label(copy[.permissionsAuthorityBoundary], systemImage: "lock.shield").font(.headline)
                    Text(copy[.permissionsAuthorityBoundaryBody]).font(.callout).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .cardStyle()
            }
            .padding(28).frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func detailCard(_ title: String, _ body: String, _ symbol: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: symbol).font(.headline)
            Text(body).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
        }
        .cardStyle()
    }

    private func scopeLabel(_ scope: PermissionScope) -> String {
        switch scope {
        case .credential: language == .simplifiedChinese ? "仅存 Keychain" : "Keychain only"
        case .execute: language == .simplifiedChinese ? "需作用域批准" : "Scoped approval"
        case .read: language == .simplifiedChinese ? "只读" : "Read-only"
        default: language == .simplifiedChinese ? "需预览与批准" : "Preview + approval"
        }
    }

    private func symbol(for scope: PermissionScope) -> String {
        switch scope {
        case .read: "eye"
        case .write: "square.and.pencil"
        case .send: "paperplane"
        case .delete: "trash"
        case .execute: "play.circle"
        case .credential: "key"
        }
    }

    private func tint(for scope: PermissionScope) -> Color {
        switch scope {
        case .read: .blue
        case .write: .green
        case .send: .purple
        case .delete: .red
        case .execute: .orange
        case .credential: .secondary
        }
    }
}

private extension View {
    func cardStyle() -> some View {
        self.padding(16)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.secondary.opacity(0.16)))
    }
}

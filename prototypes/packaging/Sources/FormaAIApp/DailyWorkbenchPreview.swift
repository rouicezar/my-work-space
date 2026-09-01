import SwiftUI
import LifecycleContract

struct DailyWorkbenchPreview: View {
    private let contract = DailyWorkbenchSurfaceContract.productDefault
    @State private var language: ProductLanguage = .simplifiedChinese
    @State private var prompt = ""
    @State private var route: PreviewComposerRoute = .localFirst
    @State private var supervisionExpanded = true
    @State private var contextPreviewPresented = false

    var body: some View {
        let copy = ProductCopy(language: language)

        VStack(spacing: 0) {
            previewDisclosure(copy)
            HStack(spacing: 0) {
                sidebar(copy)
                Divider()
                composer(copy)
                if supervisionExpanded {
                    Divider()
                    supervisionRail(copy)
                        .transition(.move(edge: .trailing).combined(with: .opacity))
                }
            }
        }
        .frame(minWidth: 900, minHeight: 620)
        .animation(.easeInOut(duration: 0.18), value: supervisionExpanded)
        .alert(copy[.contextPreviewTitle], isPresented: $contextPreviewPresented) {
            Button(copy[.dismiss], role: .cancel) {}
        } message: {
            Text(copy[.contextPreviewBody])
        }
    }

    private func previewDisclosure(_ copy: ProductCopy) -> some View {
        HStack(spacing: 10) {
            Image(systemName: "eye.trianglebadge.exclamationmark")
            Text(copy[.previewNotice]).font(.callout.weight(.semibold))
            Spacer()
            if !supervisionExpanded {
                Button { supervisionExpanded = true } label: {
                    Label(copy[.expandSupervision], systemImage: "sidebar.trailing")
                }
                .buttonStyle(.borderless)
            }
            Menu {
                Button(copy[.simplifiedChinese]) { language = .simplifiedChinese }
                Button(copy[.english]) { language = .english }
            } label: {
                Label(copy[.languageControl], systemImage: "globe")
            }
            .menuStyle(.borderlessButton)
            .fixedSize()
        }
        .padding(.horizontal, 18).padding(.vertical, 9)
        .background(Color(red: 0.96, green: 0.76, blue: 0.22))
        .foregroundStyle(.black.opacity(0.8))
    }

    private func sidebar(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 24) {
            HStack(spacing: 10) {
                Image(systemName: "sparkles.rectangle.stack.fill")
                    .font(.title2).foregroundStyle(.blue)
                Text("Forma AI").font(.headline)
            }

            VStack(alignment: .leading, spacing: 6) {
                navigationRow(copy[.newTask], "square.and.pencil", selected: true)
                navigationRow(copy[.history], "clock.arrow.circlepath", selected: false)
                navigationRow(copy[.settings], "gearshape", selected: false)
            }

            VStack(alignment: .leading, spacing: 10) {
                Text(copy[.recentTasks].uppercased())
                    .font(.caption2.monospaced().weight(.bold)).foregroundStyle(.secondary)
                Text(copy[.noRealHistory]).font(.caption).foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                VStack(alignment: .leading, spacing: 7) {
                    HStack {
                        Text(copy[.sampleBadge]).font(.caption2.monospaced().weight(.bold)).foregroundStyle(.blue)
                        Spacer()
                        Image(systemName: "doc.text.magnifyingglass").foregroundStyle(.secondary)
                    }
                    Text(copy[.sampleTask]).font(.callout.weight(.medium))
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(12)
                .background(Color.secondary.opacity(0.08), in: RoundedRectangle(cornerRadius: 12))
            }
            Spacer()
        }
        .padding(22).frame(width: 230).background(.thinMaterial)
    }

    private func navigationRow(_ title: String, _ symbol: String, selected: Bool) -> some View {
        HStack(spacing: 10) {
            Image(systemName: symbol).frame(width: 18)
            Text(title).font(.callout.weight(selected ? .semibold : .regular))
            Spacer()
        }
        .padding(.horizontal, 11).padding(.vertical, 9)
        .foregroundStyle(selected ? Color.white : Color.primary)
        .background(selected ? Color.blue : Color.clear, in: RoundedRectangle(cornerRadius: 10))
    }

    private func composer(_ copy: ProductCopy) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(copy[.newTask].uppercased())
                        .font(.caption.monospaced().weight(.bold)).foregroundStyle(.blue)
                    Text(copy[.greeting])
                        .font(.system(size: 32, weight: .semibold, design: .rounded))
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text(copy[.promptTitle]).font(.headline)
                    ZStack(alignment: .topLeading) {
                        if prompt.isEmpty {
                            Text(copy[.promptPlaceholder])
                                .foregroundStyle(.tertiary).padding(.horizontal, 6).padding(.vertical, 8)
                                .allowsHitTesting(false)
                        }
                        TextEditor(text: $prompt)
                            .font(.body).scrollContentBackground(.hidden)
                            .padding(2).frame(minHeight: 118)
                    }
                    .padding(10)
                    .background(.background, in: RoundedRectangle(cornerRadius: 15))
                    .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color.secondary.opacity(0.22)))
                    Text(copy[.promptHint]).font(.caption).foregroundStyle(.secondary)
                }

                contextCard(copy)
                routeCard(copy)

                HStack(alignment: .center, spacing: 14) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(copy[.previewPlanExplanation]).font(.caption).foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    Spacer()
                    Button(copy[.previewPlan]) {}
                        .buttonStyle(.borderedProminent).disabled(true)
                }

                VStack(alignment: .leading, spacing: 10) {
                    Text(copy[.starterTitle]).font(.headline)
                    ViewThatFits(in: .horizontal) {
                        HStack(spacing: 10) { starterCards(copy) }
                        VStack(spacing: 10) { starterCards(copy) }
                    }
                }
            }
            .padding(32).frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    @ViewBuilder
    private func starterCards(_ copy: ProductCopy) -> some View {
        starterCard(copy[.starterResearch], "books.vertical")
        starterCard(copy[.starterWriting], "doc.richtext")
        starterCard(copy[.starterPlanning], "point.3.connected.trianglepath.dotted")
    }

    private func starterCard(_ title: String, _ symbol: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Image(systemName: symbol).foregroundStyle(.blue)
            Text(title).font(.callout.weight(.medium)).fixedSize(horizontal: false, vertical: true)
        }
        .padding(14).frame(maxWidth: .infinity, minHeight: 88, alignment: .topLeading)
        .background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 13))
    }

    private func contextCard(_ copy: ProductCopy) -> some View {
        HStack(spacing: 14) {
            Image(systemName: "paperclip.circle.fill").font(.title2).foregroundStyle(.blue)
            VStack(alignment: .leading, spacing: 4) {
                Text(copy[.context]).font(.headline)
                Text(copy[.contextExplanation]).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Button(copy[.previewContext]) { contextPreviewPresented = true }
                .buttonStyle(.bordered)
        }
        .padding(16).background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 14))
    }

    private func routeCard(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Label(copy[.route], systemImage: "arrow.triangle.branch").font(.headline)
                Spacer()
                Picker(copy[.route], selection: $route) {
                    Text(copy[.localRoute]).tag(PreviewComposerRoute.localFirst)
                    Text(copy[.cloudRoute]).tag(PreviewComposerRoute.cloudProposal)
                }
                .labelsHidden().pickerStyle(.segmented).frame(maxWidth: 330)
            }
            Text(route == .localFirst ? copy[.localRouteDetail] : copy[.cloudRouteDetail])
                .font(.callout).foregroundStyle(.secondary)
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "lock.shield.fill").foregroundStyle(.green)
                VStack(alignment: .leading, spacing: 3) {
                    Text(copy[.privacyTitle]).font(.callout.weight(.semibold))
                    Text(copy[.privacyDetail]).font(.caption).foregroundStyle(.secondary)
                }
            }
        }
        .padding(18).background(.regularMaterial, in: RoundedRectangle(cornerRadius: 15))
        .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color.secondary.opacity(0.18)))
    }

    private func supervisionRail(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack {
                Text(copy[.supervision]).font(.headline)
                Spacer()
                Button { supervisionExpanded = false } label: {
                    Image(systemName: "sidebar.trailing")
                }
                .buttonStyle(.plain).help(copy[.collapseSupervision])
            }
            VStack(alignment: .leading, spacing: 8) {
                Image(systemName: "pause.circle").font(.title).foregroundStyle(.secondary)
                Text(copy[.noActiveTask]).font(.headline)
                Text(copy[.supervisionExplanation]).font(.caption).foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.vertical, 8)
            Divider()
            statusRow(copy[.agentStatus], copy[.waitingForTask], "person.2")
            statusRow(copy[.evidenceStatus], copy[.nothingProduced], "checkmark.seal")
            Spacer()
        }
        .padding(20).frame(width: 270).background(.ultraThinMaterial)
    }

    private func statusRow(_ title: String, _ value: String, _ symbol: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: symbol).foregroundStyle(.secondary).frame(width: 18)
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.caption.weight(.semibold))
                Text(value).font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}

private enum PreviewComposerRoute: Hashable {
    case localFirst
    case cloudProposal
}

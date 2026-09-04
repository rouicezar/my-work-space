import SwiftUI

struct ResizableWorkbenchLayout<Sidebar: View, Content: View, Trailing: View>: View {
    @Binding var sidebarWidth: CGFloat
    @Binding var trailingWidth: CGFloat
    let trailingVisible: Bool
    @ViewBuilder let sidebar: () -> Sidebar
    @ViewBuilder let content: () -> Content
    @ViewBuilder let trailing: () -> Trailing

    var body: some View {
        HStack(spacing: 0) {
            sidebar()
                .frame(width: sidebarWidth)
            resizeDivider { delta in
                sidebarWidth = clamp(sidebarWidth + delta, 190, 360)
            }
            content()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            if trailingVisible {
                resizeDivider { delta in
                    trailingWidth = clamp(trailingWidth - delta, 220, 460)
                }
                trailing()
                    .frame(width: trailingWidth)
            }
        }
    }

    private func resizeDivider(onDrag: @escaping (CGFloat) -> Void) -> some View {
        ResizeDivider(onDrag: onDrag)
    }

    private struct ResizeDivider: View {
        let onDrag: (CGFloat) -> Void
        @State private var lastTranslation: CGFloat = 0

        var body: some View {
            Rectangle()
                .fill(Color.secondary.opacity(0.18))
                .frame(width: 5)
                .overlay {
                    Rectangle()
                        .fill(Color.clear)
                        .frame(width: 10)
                        .contentShape(Rectangle())
                        .gesture(
                            DragGesture(minimumDistance: 0)
                                .onChanged { value in
                                    let delta = value.translation.width - lastTranslation
                                    lastTranslation = value.translation.width
                                    onDrag(delta)
                                }
                                .onEnded { _ in
                                    lastTranslation = 0
                                }
                        )
                        .onHover { hovering in
                            if hovering {
                                NSCursor.resizeLeftRight.push()
                            } else {
                                NSCursor.pop()
                            }
                        }
                }
        }
    }

    private func clamp(_ value: CGFloat, _ lower: CGFloat, _ upper: CGFloat) -> CGFloat {
        min(max(value, lower), upper)
    }
}

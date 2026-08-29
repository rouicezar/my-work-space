// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "MacAIWorkOSPackagingPrototype",
    platforms: [.macOS(.v15)],
    products: [
        .library(name: "LifecycleContract", targets: ["LifecycleContract"]),
        .library(name: "RuntimeSecurity", targets: ["RuntimeSecurity"]),
        .executable(name: "mac-ai-work-os-launcher", targets: ["MacAIWorkOSLauncher"]),
        .executable(name: "MacAIWorkOSApp", targets: ["MacAIWorkOSApp"]),
    ],
    targets: [
        .target(name: "LifecycleContract"),
        .target(name: "RuntimeSecurity"),
        .executableTarget(
            name: "MacAIWorkOSLauncher",
            dependencies: ["LifecycleContract"]
        ),
        .executableTarget(
            name: "MacAIWorkOSApp",
            dependencies: ["LifecycleContract"]
        ),
        .testTarget(
            name: "LifecycleContractTests",
            dependencies: ["LifecycleContract"]
        ),
        .testTarget(
            name: "RuntimeSecurityTests",
            dependencies: ["RuntimeSecurity"]
        ),
    ]
)

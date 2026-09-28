#pragma once

#include "oot3d/renderer/azahar_texture_pack.h"
#include <imgui.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace Fast::Oot3d {

namespace detail {

inline std::vector<std::filesystem::path> GetDataRoots() {
    std::vector<std::filesystem::path> roots;
    std::error_code ec;

    if (const char* env = std::getenv("TRIAEVUM_DATA_DIR"); env && *env) {
        roots.push_back(std::filesystem::path(env));
    }
#if defined(_WIN32)
    if (const char* appData = std::getenv("APPDATA"); appData && *appData) {
        roots.push_back(std::filesystem::path(appData) / "TriAevum");
    }
#else
    if (const char* home = std::getenv("HOME"); home && *home) {
        roots.push_back(std::filesystem::path(home) / ".var/app/io.github.coccofresco.TriAevum/data/TriAevum");
        roots.push_back(std::filesystem::path(home) / ".local/share/TriAevum");
    }
    if (const char* xdg = std::getenv("XDG_DATA_HOME"); xdg && *xdg) {
        roots.push_back(std::filesystem::path(xdg) / "TriAevum");
    }
#endif
    roots.push_back(std::filesystem::current_path(ec) / "data" / "TriAevum");
    roots.push_back(std::filesystem::current_path(ec));
    return roots;
}

inline std::vector<std::filesystem::path> FindActiveUiDirectories(const std::filesystem::path& loadDir) {
    std::vector<std::filesystem::path> dirs;
    std::error_code ec;

    if (!loadDir.empty()) {
        auto candidate1 = loadDir / "load" / "textures" / "0004000000033600" / "UI";
        if (std::filesystem::exists(candidate1, ec)) dirs.push_back(candidate1);

        auto candidate2 = loadDir / "UI";
        if (std::filesystem::exists(candidate2, ec) && candidate2 != candidate1) dirs.push_back(candidate2);

        auto candidate3 = loadDir / "textures" / "0004000000033600" / "UI";
        if (std::filesystem::exists(candidate3, ec) && candidate3 != candidate1 && candidate3 != candidate2) dirs.push_back(candidate3);
    }

    for (const auto& root : GetDataRoots()) {
        auto p1 = root / "textures" / "load" / "textures" / "0004000000033600" / "UI";
        if (std::filesystem::exists(p1, ec) && std::find(dirs.begin(), dirs.end(), p1) == dirs.end()) {
            dirs.push_back(p1);
        }
        auto p2 = root / "load" / "textures" / "0004000000033600" / "UI";
        if (std::filesystem::exists(p2, ec) && std::find(dirs.begin(), dirs.end(), p2) == dirs.end()) {
            dirs.push_back(p2);
        }
    }

    return dirs;
}

inline std::filesystem::path FindPacksRootDir(const std::filesystem::path& loadDir) {
    std::error_code ec;
    if (const char* env = std::getenv("TRIAEVUM_TEXTURE_PACKS_DIR"); env && *env) {
        if (std::filesystem::exists(env, ec)) return env;
    }
    if (!loadDir.empty()) {
        auto candidate = loadDir.parent_path() / "texture_packs";
        if (std::filesystem::exists(candidate, ec)) return candidate;
        candidate = loadDir / ".." / "texture_packs";
        if (std::filesystem::exists(candidate, ec)) return candidate;
    }
    for (const auto& root : GetDataRoots()) {
        auto candidate = root / "texture_packs";
        if (std::filesystem::exists(candidate, ec)) return candidate;
    }
    return {};
}

inline std::filesystem::path FindPackSourceDir(const std::filesystem::path& packsRoot, const std::string& packName) {
    std::error_code ec;
    auto candidate = packsRoot / packName / "load" / "textures" / "0004000000033600" / "UI";
    if (std::filesystem::exists(candidate, ec)) return candidate;
    candidate = packsRoot / packName / "UI";
    if (std::filesystem::exists(candidate, ec)) return candidate;
    candidate = packsRoot / packName;
    if (std::filesystem::exists(candidate, ec)) return candidate;
    return {};
}

inline int DetectActiveControllerStyle(const std::filesystem::path& loadDir) {
    const auto activeDirs = FindActiveUiDirectories(loadDir);
    for (const auto& dir : activeDirs) {
        std::ifstream marker(dir / ".active_controller_style");
        if (marker.is_open()) {
            std::string line;
            if (std::getline(marker, line)) {
                if (line.find("ps5") != std::string::npos) return 0;
                if (line.find("xbox") != std::string::npos) return 1;
                if (line.find("nintendo") != std::string::npos) return 2;
            }
        }
    }
    for (const auto& dir : activeDirs) {
        std::error_code ec;
        auto mainTex = dir / "tex1_512x256_7D6716CEB0D7F7FA_4_mip0.png";
        if (std::filesystem::exists(mainTex, ec)) {
            auto size = std::filesystem::file_size(mainTex, ec);
            if (size > 7000000) return 0;
            if (size > 1000000 && size < 7000000) return 1;
        }
    }
    return 0; // Default to PS5
}

inline bool ApplyControllerPromptPack(int styleIndex, std::string* statusOut = nullptr) {
    static const char* kStyleNames[] = {"ps5", "xbox", "nintendo"};
    if (styleIndex < 0 || styleIndex >= 3) return false;

    const std::string packName = kStyleNames[styleIndex];
    const auto status = ::Oot3d::Renderer::AzaharTexturePackRuntime::Instance().Snapshot();
    const auto activeDirs = FindActiveUiDirectories(status.LoadDirectory);
    const auto packsRoot = FindPacksRootDir(status.LoadDirectory);

    if (activeDirs.empty() || packsRoot.empty()) {
        if (statusOut) *statusOut = "Error: Paths not found for UI textures or packs";
        return false;
    }

    const auto sourceDir = FindPackSourceDir(packsRoot, packName);
    if (sourceDir.empty()) {
        if (statusOut) *statusOut = "Error: Pack folder not found for " + packName;
        return false;
    }

    std::error_code ec;
    for (const auto& targetDir : activeDirs) {
        std::filesystem::create_directories(targetDir, ec);
        for (const auto& entry : std::filesystem::recursive_directory_iterator(
                 sourceDir, std::filesystem::directory_options::skip_permission_denied, ec)) {
            if (ec) break;
            const auto relPath = std::filesystem::relative(entry.path(), sourceDir, ec);
            if (ec) continue;
            const auto destPath = targetDir / relPath;
            if (entry.is_directory(ec)) {
                std::filesystem::create_directories(destPath, ec);
            } else if (entry.is_regular_file(ec)) {
                std::filesystem::create_directories(destPath.parent_path(), ec);
                std::filesystem::copy_file(entry.path(), destPath, std::filesystem::copy_options::overwrite_existing, ec);
            }
        }
        std::ofstream marker(targetDir / ".active_controller_style");
        if (marker.is_open()) {
            marker << packName << "\n";
        }
    }

    // Copy TopScreen binary override pack (.o3tu) across active roots
    for (const auto& root : GetDataRoots()) {
        const auto topscreenPacksDir = root / "mods" / "topscreen" / "packs";
        const auto o3tuSrc = topscreenPacksDir / ("atlas_overrides_" + packName + ".o3tu");
        if (std::filesystem::exists(o3tuSrc, ec)) {
            const auto topscreenDir = root / "mods" / "topscreen";
            for (const auto& entry : std::filesystem::directory_iterator(topscreenDir, ec)) {
                if (entry.is_directory(ec)) {
                    const auto targetFile = entry.path() / "atlas_overrides.o3tu";
                    if (std::filesystem::exists(targetFile, ec)) {
                        std::filesystem::copy_file(o3tuSrc, targetFile,
                                                   std::filesystem::copy_options::overwrite_existing, ec);
                    }
                }
            }
        }

        // Synchronize DualSense motion and GUID settings in controls.json
        const auto controlsJsonPath = root / "config" / "controls.json";
        if (std::filesystem::exists(controlsJsonPath, ec)) {
            try {
                std::ifstream inFile(controlsJsonPath);
                if (inFile.is_open()) {
                    nlohmann::json cfg;
                    inFile >> cfg;
                    inFile.close();
                    cfg["controller_guid"] = "";
                    if (cfg.contains("aim")) cfg["aim"]["source"] = "automatic";
                    if (cfg.contains("calibration")) cfg["calibration"]["controller_guid"] = "";
                    std::ofstream outFile(controlsJsonPath);
                    if (outFile.is_open()) {
                        outFile << cfg.dump(2) << "\n";
                    }
                }
            } catch (...) {}
        }
    }

    // Trigger immediate texture reload in Azahar runtime
    ::Oot3d::Renderer::AzaharTexturePackRuntime::Instance().Reload();

    if (statusOut) {
        if (styleIndex == 0) *statusOut = "PlayStation 5 (DualSense: ✖ ⭘ ◼ ▲) buttons applied!";
        else if (styleIndex == 1) *statusOut = "Xbox Series / One buttons applied!";
        else *statusOut = "Nintendo Original buttons applied!";
    }
    return true;
}

} // namespace detail

inline int& ActiveControllerPromptIndex() {
    static int sCurrentStyle = -1;
    return sCurrentStyle;
}

inline bool DrawControllerPromptSelector(std::string* statusMessage = nullptr) {
    int& currentStyle = ActiveControllerPromptIndex();
    static std::string sLocalStatus;
    auto& runtime = ::Oot3d::Renderer::AzaharTexturePackRuntime::Instance();
    const auto snapshot = runtime.Snapshot();

    if (currentStyle < 0) {
        currentStyle = detail::DetectActiveControllerStyle(snapshot.LoadDirectory);
    }

    constexpr const char* kPromptStyles[] = {
        "PlayStation 5 (DualSense: Cross, Circle, Square, Triangle, L1/R1, L2/R2)",
        "Xbox Series / One (A, B, X, Y, LB/RB, LT/RT)",
        "Nintendo Original (A, B, X, Y, L/R, ZL/ZR)"
    };

    bool changed = false;
    int selected = currentStyle;
    ImGui::TextUnformatted("Button Prompts UI");
    ImGui::SetNextItemWidth(ImGui::GetContentRegionAvail().x * 0.76F);
    if (ImGui::Combo("##ControllerPromptStyle", &selected, kPromptStyles, 3)) {
        if (selected != currentStyle) {
            currentStyle = selected;
            std::string applyStatus;
            detail::ApplyControllerPromptPack(currentStyle, &applyStatus);
            sLocalStatus = applyStatus;
            if (statusMessage) *statusMessage = applyStatus;
            changed = true;
        }
    }
    ImGui::SameLine();
    if (ImGui::Button("Reload##PromptsReload")) {
        std::string applyStatus;
        detail::ApplyControllerPromptPack(currentStyle, &applyStatus);
        sLocalStatus = applyStatus;
        if (statusMessage) *statusMessage = applyStatus;
        changed = true;
    }
    if (ImGui::IsItemHovered()) {
        ImGui::SetTooltip("Force-reload active controller button textures into VRAM");
    }

    if (!sLocalStatus.empty()) {
        ImGui::TextColored(ImVec4(0.35F, 0.88F, 0.45F, 1.0F), "%s", sLocalStatus.c_str());
    }
    return changed;
}

} // namespace Fast::Oot3d

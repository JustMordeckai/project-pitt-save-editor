"""Reference data extracted from the game (build 1.0.5)."""

PHASES = (0, 1, 2, 3, 4)  # the game clamps a saved phase of 5 back to 4 on load

FLAGS = (
    "torch_unlocked", "uv_unlocked", "uv_lamp_dispensed", "pickaxe_found",
    "elevator_hacked", "keypad_revealed", "secret_ending_seen",
)

RESOURCE_FIELDS = ("money", "bank", "mining_bank", "total_money_gained", "total_money_spent")

LEVEL_CATEGORIES = ("upgrades", "tools", "toys", "combos", "products")

# Milestone ids from scripts/unlock_manager.gdc, in declaration order.
MILESTONES = (
    "unlock_sprint", "unlock_jump", "unlock_crouch", "unlock_throw",
    "unlock_box", "unlock_ducks", "unlock_throw_lvl2", "unlock_broom",
    "unlock_sponge", "unlock_equip", "unlock_combo_tab", "unlock_throw_lvl3",
    "unlock_sticky_tools", "unlock_reset_rotation", "unlock_prop_surf", "unlock_snap_grid",
    "unlock_panel", "unlock_ducks_craft_speed_2", "unlock_ducks_craft_value_2", "unlock_sprint_lvl2",
    "unlock_combo_lvl2", "unlock_ducks_auto_machine", "unlock_jump_lvl2", "unlock_slide",
    "unlock_fan", "unlock_ducks_craft_speed_3", "unlock_ducks_craft_value_3", "unlock_chain_combos",
    "unlock_crouch_lvl2", "unlock_combo_lvl3", "unlock_ducks_auto_machine_2", "unlock_luck",
    "unlock_magnet", "unlock_box_lvl2", "unlock_chain_combos_lvl2", "unlock_panel_lvl2",
    "unlock_panel_lvl3", "unlock_combo_lvl4", "unlock_sprint_lvl3", "unlock_ducks_auto_machine_3",
    "unlock_crouch_lvl3", "unlock_press", "unlock_chain_combos_lvl3", "unlock_combo_lvl5",
    "unlock_gambling_crate", "unlock_gambling_metal_crate", "unlock_gambling_plush_crate", "unlock_gambling_anomaly_crate",
    "unlock_slide_lvl2", "unlock_golf_club", "unlock_remote", "unlock_bumper",
    "unlock_luck_lvl2", "unlock_luck_lvl3", "unlock_luck_lvl4", "unlock_luck_lvl5",
    "unlock_luck_lvl6", "unlock_luck_lvl7", "unlock_luck_lvl8", "unlock_luck_lvl9",
    "unlock_luck_lvl10", "unlock_stat_sign", "unlock_feed_tools", "unlock_box_lvl3",
    "unlock_box_lvl4", "unlock_broom_lvl2", "unlock_phase2_product", "unlock_broom_lvl3",
    "unlock_fan_lvl2", "unlock_fan_lvl3", "unlock_magnet_lvl2", "unlock_piston_lvl2",
    "unlock_piston", "unlock_bowling_pin_set", "unlock_panel_cushion", "unlock_panel_cushion_2",
    "unlock_panel_slick", "unlock_panel_slick_2", "unlock_crown_craft_speed_1", "unlock_crown_craft_value_1",
    "unlock_crown_auto_machine", "unlock_crown_auto_machine_2", "unlock_crown_auto_machine_3", "unlock_basketball_hoop",
    "unlock_speed_radar", "unlock_crown_craft_speed_2", "unlock_crown_craft_value_2", "unlock_crown_craft_speed_3",
    "unlock_crown_craft_value_3", "unlock_phase3_product", "unlock_bear_craft_speed_1", "unlock_bear_craft_value_1",
    "unlock_bear_craft_speed_2", "unlock_bear_craft_value_2", "unlock_bear_craft_speed_3", "unlock_bear_craft_value_3",
    "unlock_bear_auto_machine", "unlock_bear_auto_machine_2", "unlock_bear_auto_machine_3", "unlock_spring_pad",
    "unlock_vacuum", "unlock_qa_arm", "unlock_cannon", "unlock_mega_combo",
    "unlock_mega_combo_lvl2", "unlock_mega_combo_lvl3", "unlock_phase4_product", "unlock_anomaly_craft_speed_1",
    "unlock_anomaly_craft_value_1", "unlock_anomaly_craft_speed_2", "unlock_anomaly_craft_value_2", "unlock_anomaly_craft_speed_3",
    "unlock_anomaly_craft_value_3", "unlock_tractor_beam", "unlock_gravity_inverter", "unlock_orbit_tool",
    "unlock_portal", "unlock_piston_lvl3", "unlock_spring_pad_lvl2", "unlock_vacuum_lvl2",
    "unlock_cannon_lvl2", "unlock_disco_ball", "unlock_golden_duck_statue", "unlock_trading_terminal",
    "unlock_auto_crafter", "unlock_scheduler", "unlock_remote_tier2", "unlock_remote_tier3",
    "unlock_remote_tier4", "unlock_stat_sign_big", "unlock_feed_screen_big", "unlock_pickaxe_rebuy",
    "unlock_panel_rack", "unlock_panel_rack_lvl2", "unlock_panel_rack_lvl3",
)

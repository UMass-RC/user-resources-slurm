use nix::unistd::{Uid, User};
use serde_json::Value;
use std::collections::HashMap;
use std::env;
use std::io::{self};
use std::process::{Command, Output};

fn assert_command_success(output: &Output) {
    assert!(
        output.status.success(),
        "command failed!\n{}\nstdout:\n{}\nstderr:\n{}\n",
        output.status,
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

fn get_all_user_association_accounts(username: &String) -> Vec<String> {
    let mut cmd = Command::new("/usr/bin/sacctmgr");
    let args = [
        "--json",
        "show",
        "association",
        "where",
        &format!("user={}", username),
    ];
    cmd.args(args);
    // println!("executing sacctmgr with args: {:?}", args);
    let output: Output = cmd.output().unwrap();
    assert_command_success(&output);

    let stdout_parsed: HashMap<String, Value> = serde_json::from_slice(&output.stdout).unwrap();
    let user_associations: &Vec<Value> = stdout_parsed["associations"].as_array().unwrap();
    let accounts: Vec<String> = user_associations
        .iter()
        .filter_map(|assoc| assoc["account"].as_str().map(|x| x.to_string()))
        .collect::<Vec<String>>();
    return accounts;
}

fn get_default_account(username: &String) -> String {
    let mut cmd = Command::new("/usr/bin/sacctmgr");
    let args = [
        "--json",
        "show",
        "user",
        "where",
        &format!("name={}", username),
    ];
    cmd.args(args);
    // println!("executing sacctmgr with args: {:?}", args);
    let output: Output = cmd.output().unwrap();
    assert_command_success(&output);

    let stdout_parsed: HashMap<String, Value> = serde_json::from_slice(&output.stdout).unwrap();
    let users: &Vec<Value> = stdout_parsed["users"].as_array().unwrap();
    assert_eq!(
        users.len(),
        1,
        "exactly 1 user must be found with given name."
    );
    let this_user = &users[0];
    return this_user["default"]["account"]
        .as_str()
        .unwrap()
        .to_string();
}

fn set_default_account(username: &String, account: &String) {
    let mut sacctmgr_modify_cmd = Command::new("/usr/bin/sacctmgr");
    let sacctmgr_modify_args = [
        "modify",
        "--immediate",
        "user",
        "where",
        &format!("name={}", username),
        "set",
        &format!("defaultAccount={}", account),
    ];
    sacctmgr_modify_cmd.args(sacctmgr_modify_args);
    // println!("executing sacctmgr with args: {:?}", sacctmgr_modify_args);
    let sacctmgr_modify_output: Output = sacctmgr_modify_cmd.output().unwrap();
    assert_command_success(&sacctmgr_modify_output);
    println!(
        "{}",
        String::from_utf8_lossy(&sacctmgr_modify_output.stdout)
    );
}

fn main() -> io::Result<()> {
    let username: String = User::from_uid(Uid::current()).unwrap().unwrap().name;
    let effective_username: String = User::from_uid(Uid::effective()).unwrap().unwrap().name;
    assert_eq!(
        effective_username, "slurm",
        "This binary must be owned by \"slurm\" with the suid bit set!"
    );
    assert_ne!(username, "root", "This program must not be run as root!");

    let current_default_account = get_default_account(&username);
    let valid_accounts = get_all_user_association_accounts(&username);
    let help_msg = format!(
        "\
            exactly one argument required (account name).\n\
            current default account name for this user: \"{}\"\n\
            valid account names for this user: {:?}\n\
        ",
        current_default_account, valid_accounts
    );

    let args: Vec<String> = env::args().collect();
    assert!(args.len() == 2, "{}", help_msg);
    let account: &String = &args[1];
    if *account == current_default_account {
        println!("this account is already the default.");
        return Ok(());
    }
    assert!(
        valid_accounts.contains(account),
        "invalid account name: \"{}\"\n\n{}",
        account,
        help_msg
    );
    set_default_account(&username, &account);

    Ok(())
}

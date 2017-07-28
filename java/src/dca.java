import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;
import net.sourceforge.argparse4j.inf.Subparser;
import net.sourceforge.argparse4j.inf.Subparsers;

import javax.json.Json;
import javax.json.JsonArrayBuilder;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;
import javax.json.JsonWriter;
import javax.json.stream.JsonGenerator;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;

import static net.sourceforge.argparse4j.impl.Arguments.storeTrue;

class StatusMessage {
    private JsonObject status;

    StatusMessage() {
        this(true, "", Json.createObjectBuilder());
    }
    StatusMessage(String error) {
        this(false, error, Json.createObjectBuilder());
    }
    StatusMessage(JsonObjectBuilder builder) {
        this(true, "", builder);
    }
    private StatusMessage(boolean success, String error, JsonObjectBuilder builder) {
        status = builder.add("status", (success ? "success" : "failed"))
                .add("error", (error.equals("") ? "no error" : error))
                .build();
    }

    void pprint() {
        StringWriter sw = new StringWriter();

        Map<String, Object> properties = new HashMap<>();
        properties.put(JsonGenerator.PRETTY_PRINTING, true);
        JsonWriter writer = Json.createWriterFactory(properties).createWriter(sw);

        writer.writeObject(status);
        writer.close();

        System.out.println(sw.toString());
    }
    void print() {
        System.out.println(status);
    }
}

abstract class Command {
    DateTimeFormatter format = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    DateTimeFormatter billFormat = DateTimeFormatter.ofPattern("yyyy-MM-dd");
    Connection c;

    StatusMessage insufficientPermissions = new StatusMessage("insufficient permissions");
    // special verify for user commands - admins can obviously run them
    boolean verify(ResultSet projectRS) throws SQLException {
        String username = System.getProperty("user.name");
        ArrayList<String> users = fromCSV(projectRS.getString("users"));
        if (caseInsensitiveContains(users, username)) {
            return true;
        }
        return verify(false, true);
    }
    // all commands are admin commands EXCEPT dca role add/delete admin
    boolean verify(boolean tenantadminCommand, boolean adminCommand) throws SQLException {
        // incredibly insecure way of obtaining linux login username - there are many ways to circumvent this method
        String username = System.getProperty("user.name");

        if (!username.equalsIgnoreCase("root")) {
            ResultSet rs = select("role", "name='" + username + "'");
            if (!rs.next()
                    || !(rs.getBoolean("tenantadmin") && tenantadminCommand
                    || rs.getBoolean("admin") && adminCommand)) {
                return false;
            }
        }
        return true;
    }
    boolean verifyRoot() {
        return System.getProperty("user.name").equalsIgnoreCase("root");
    }
    abstract StatusMessage execute(Namespace ns, Connection c) throws SQLException;

    /***** UTILITY *****/

    boolean isInt(String s) {
        try {
            Integer.parseInt(s);
            return true;
        } catch (RuntimeException e) {
            return false;
        }
    }
    boolean isAlnum(String s) {
        return s.matches("^[^_\\W]*$");
    }
    boolean isMoney(float val) {
        return val >= 0;
    }
    // rounds to 2 decimal points
    String round(float val) {
        return String.format("%.2f", val);
    }
    // not to be confused with isdate, istime checks an integer difference in time measured in seconds
    boolean isTime(int val) {
        return val >= 0;
    }
    // works with strings using date format, non-negative integers (epoch time)
    boolean isDate(String s) {
        try {
            LocalDate.parse(s, billFormat);
            return true;
        } catch (DateTimeParseException e) {
            return false;
        }
    }
    boolean isDateTime(String s) {
        if (isInt(s)) {
            return Integer.parseInt(s) >= 0;
        }
        try {
            LocalDateTime.parse(s, format);
            return true;
        } catch (DateTimeParseException e) {
            return false;
        }
    }
    LocalDateTime toDateTime(Timestamp t) {
        return t.toLocalDateTime();
    }
    LocalDateTime toDate(String s) {
        return LocalDate.parse(s, billFormat).atStartOfDay();
    }
    LocalDateTime toDateTime(String s) {
        if (isInt(s)) {
            return LocalDateTime.from(Instant.ofEpochSecond(Integer.parseInt(s)).atZone(ZoneId.systemDefault()));
        }
        return LocalDateTime.parse(s, format);
    }
    LocalDateTime now() {
        return LocalDateTime.now();
    }
    // returns a string representing the current time in the format yyyy-MM-dd HH:mm:ss
    String nowString() {
        return LocalDateTime.now().format(format);
    }

    boolean caseInsensitiveContains(ArrayList<String> list, String match) {
        for (String s : list) {
            if (match.equalsIgnoreCase(s)) {
                return true;
            }
        }
        return false;
    }

    // Used when disabling tenant/project, double checks that the user wants to do something
    boolean confirmation() {
        System.out.print("Are you sure? (y/n) ");
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        try {
            return in.readLine().toLowerCase().equals("y");
        } catch(IOException e) {
            e.printStackTrace();
            System.exit(1);
        }
        return false;
    }

    // Checks if a tenant has sufficient balance/credit to support a budget shift or a new project
    StatusMessage sufficientBalCredit(String tenant, float tenantBalance, float tenantCredit,
                                float initialBalance, float initialCredit) throws SQLException {
        ResultSet projectRS = select("project", "tenant='" + tenant + "'");
        float totalBalance = initialBalance, totalCredit = initialCredit;
        while (projectRS.next()) {
            totalBalance += projectRS.getFloat("balance");
            totalCredit += projectRS.getFloat("credit");
        }
        if (totalBalance > tenantBalance) {
            return new StatusMessage("insufficient balance in tenant");
        }
        if (totalCredit > tenantCredit) {
            return new StatusMessage("insufficient credit in tenant");
        }
        return null;
    }
    
    /***** JSON *****/
    JsonObjectBuilder tenantBuilder(ResultSet rs, JsonArrayBuilder projectJsonBuilder) throws SQLException {
        return Json.createObjectBuilder()
                .add("name", rs.getString("name"))
                .add("balance", rs.getFloat("balance"))
                .add("credit", rs.getFloat("credit"))
                .add("projects", projectJsonBuilder);
    }
    JsonObjectBuilder projectBuilder(ResultSet rs, ArrayList<String> users) throws SQLException {
        return Json.createObjectBuilder()
                .add("tenant", rs.getString("tenant"))
                .add("project", rs.getString("project"))
                .add("balance", rs.getFloat("balance"))
                .add("credit", rs.getFloat("credit"))
                .add("requested", rs.getFloat("requested"))
                .add("rate", rs.getFloat("rate"))
                .add("users", usersBuilder(users));
    }
    private JsonArrayBuilder usersBuilder(ArrayList<String> users) {
        JsonArrayBuilder userJsonBuilder = Json.createArrayBuilder();
        for (String user : users) {
            userJsonBuilder.add(user);
        }
        return userJsonBuilder;
    }
    // Converts from csv (comma-separated values) string to a List
    ArrayList<String> fromCSV(String s) {
        if (s.equals("")) {
            return new ArrayList<>();
        }
        return new ArrayList<>(Arrays.asList(s.split("\\s+,\\s+")));
    }
    String toCSV(ArrayList<String> list) {
        return list.toString().replaceAll("[\\[.\\].\\s+]", "");
    }

    /***** SQL *****/

    void create(String table, String columns) throws SQLException {
        c.createStatement().execute("CREATE TABLE " + table + "(" + columns + ")");
    }
    ResultSet select(String table) throws SQLException {
        return c.createStatement().executeQuery("SELECT * FROM " + table);
    }
    ResultSet select(String table, String condition) throws SQLException {
        return c.createStatement().executeQuery("SELECT * FROM " + table + " WHERE " + condition);
    }
    void insert(String table, String columns, String values) throws SQLException {
        c.createStatement().execute("INSERT INTO " + table + " (" + columns + ") VALUES (" + values + ")");
    }
    void update(String table, String columns) throws SQLException {
        c.createStatement().executeUpdate("UPDATE " + table + " SET " + columns);
    }
    void update(String table, String columns, String condition) throws SQLException {
        c.createStatement().executeUpdate("UPDATE " + table + " SET " + columns + " WHERE " + condition);
    }
    void log(String category, String action, String details) throws SQLException {
        insert("log", "category,action,details,date", "'" + category + "','" + action
                        + "','" + details + "','" + nowString() + "'");
    }
}

class WipeSQL extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verifyRoot()) {
            return insufficientPermissions;
        }

        Statement s = c.createStatement();
        s.execute("DROP TABLE tenant");
        s.execute("DROP TABLE project");
        s.execute("DROP TABLE payment");
        s.execute("DROP TABLE transaction");
        s.execute("DROP TABLE log");
        s.execute("DROP TABLE rate");
        s.execute("DROP TABLE role");
        return new StatusMessage();
    }
}

class SetupSQL extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verifyRoot()) {
            return insufficientPermissions;
        }

        Statement s = c.createStatement();
        ResultSet rs = s.executeQuery("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'dca';");
        rs.next();
        if (rs.getInt(1) != 0) {
            return new StatusMessage("MySQL has already been setup");
        }
        create("tenant", "name VARCHAR(32),balance FLOAT,credit FLOAT,projects VARCHAR(4096),d BOOLEAN");
        create("project", "tenant VARCHAR(32),project VARCHAR(32),balance FLOAT,credit FLOAT,"
                + "requested FLOAT,rate FLOAT,users VARCHAR(4096),d BOOLEAN");
        create("transaction", "project VARCHAR(32),user VARCHAR(32),start DATETIME,end DATETIME,"
                + "runtime INT,cost FLOAT");
        create("payment", "tenant VARCHAR(32),date DATETIME,payment FLOAT");
        create("rate", "rate FLOAT");
        create("log", "category VARCHAR(32),action VARCHAR(32),details VARCHAR(4096),date DATETIME");
        create("role", "name VARCHAR(32),tenantadmin BOOLEAN,admin BOOLEAN");
        insert("rate", "rate", "0");

        return new StatusMessage();
    }
}

class AddTenant extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(false, true)) {
            return insufficientPermissions;
        }

        String tenant = ns.getString("tenant");
        ResultSet rs = select("tenant", "name='" + tenant + "'");
        if (rs.next()) {
            if (rs.getBoolean("d")) {
                return new StatusMessage("existing disabled tenant");
            }
            return new StatusMessage("tenant already exists");
        }
        if (!(tenant.length() <= 32 && isAlnum(tenant))) {
            return new StatusMessage("invalid tenant name");
        }
        float credit = ns.getFloat("credit");
        if (!isMoney(credit)) {
            return new StatusMessage("invalid credit amount");
        }

        insert("tenant", "name,balance,credit,projects,d", "'" + tenant + "',0.0," + credit
                + ",'',false");
        log("tenant", "add", "name:" + tenant + ", credit:" + credit);
        return new StatusMessage();
    }
}

class DisableTenant extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(false, true)) {
            return insufficientPermissions;
        }

        if (!ns.getBoolean("y") && !confirmation()) {
            return new StatusMessage("failed to disable: no confirmation");
        }

        String tenant = ns.getString("tenant");
        ResultSet rs = select("tenant", "name='" + tenant + "'");
        if (!rs.next()) {
            return new StatusMessage("tenant does not exist");
        }
        if (rs.getBoolean("d")) {
            return new StatusMessage("tenant is already disabled");
        }

        ResultSet projectRS = select("project", "tenant='" + tenant + "'");
        while (projectRS.next()) {
            if (projectRS.getFloat("requested") != 0) {
                return new StatusMessage("tenant has a project with pending transactions");
            }
        }

        update("project", "d=true", "tenant='" + tenant + "'");
        update("tenant", "d=true", "name='" + tenant + "'");
        log("tenant", "disable", "name: " + tenant);
        return new StatusMessage();
    }
}

class ModifyTenant extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(false, true)) {
            return insufficientPermissions;
        }

        String tenant = ns.getString("tenant");
        ResultSet rs = select("tenant", "name='" + tenant + "'");
        if (!rs.next()) {
            return new StatusMessage("tenant does not exist");
        }
        if (rs.getBoolean("d")) {
            return new StatusMessage("tenant is disabled");
        }
        float credit = ns.getFloat("credit");
        if (!isMoney(credit)) {
            return new StatusMessage("invalid credit amount");
        }
        rs = select("project", "d=false AND tenant='" + tenant + "'");
        float totalCredit = 0;
        while (rs.next()) {
            totalCredit += rs.getFloat("credit");
        }
        if (totalCredit > credit) {
            return new StatusMessage("too much credit allocated to projects; try again with more credit");
        }

        update("tenant", "credit=" + credit, "name='" + tenant + "'");
        log("tenant", "modify", "name: " + tenant + ", credit: " + credit);
        return new StatusMessage();
    }
}

class PaymentTenant extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(false, true)) {
            return insufficientPermissions;
        }

        String tenant = ns.getString("tenant");
        ResultSet rs = select("tenant", "name='" + tenant + "'");
        if (!rs.next()) {
            return new StatusMessage("tenant does not exist");
        }
        if (rs.getBoolean("d")) {
            return new StatusMessage("tenant is disabled");
        }
        float payment = ns.getFloat("payment");
        if (!isMoney(payment)) {
            return new StatusMessage("invalid payment");
        }

        float balance = rs.getFloat("balance");
        update("tenant", "balance=" + (balance + payment), "name='" + tenant + "'");
        insert("payment", "tenant,date,payment", "'" + tenant + "','" + nowString()
                + "'," + payment);
        log("tenant", "payment", "name: " + tenant + ", payment: " + payment);
        return new StatusMessage();
    }
}

class AddProject extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(true, true)) {
            return insufficientPermissions;
        }

        String tenant = ns.getString("tenant");
        ResultSet tenantRS = select("tenant", "name='" + tenant + "'");
        if (!tenantRS.next()) {
            return new StatusMessage("tenant does not exist");
        }
        if (tenantRS.getBoolean("d")) {
            return new StatusMessage("tenant is disabled");
        }

        String project = ns.getString("project");
        ResultSet projectRS = select("project", "project='" + project + "'");
        if (projectRS.next()) {
            if (projectRS.getBoolean("d")) {
                return new StatusMessage("existing disabled project");
            }
            return new StatusMessage("project already exists");
        }
        if (!(project.length() <= 32 && isAlnum(project))) {
            return new StatusMessage("invalid project name");
        }

        float balance = ns.getFloat("balance");
        float credit = ns.getFloat("credit");
        if (!(isMoney(balance) && isMoney(credit))) {
            return new StatusMessage("invalid budget");
        }
        
        StatusMessage sm = sufficientBalCredit(tenant, tenantRS.getFloat("balance"),
                tenantRS.getFloat("credit"), balance, credit);
        if (sm != null) {
            return sm;
        }

        ResultSet rs = select("rate");
        rs.next();
        float rate = rs.getFloat("rate");

        ArrayList<String> projects = fromCSV(tenantRS.getString("projects"));
        projects.add(project);
        update("tenant", "projects='" + toCSV(projects) + "'", "name='" + tenant + "'");
        insert("project", "tenant,project,balance,credit,requested,rate,users,d",
                "'" + tenant + "','" + project + "'," + balance + "," + credit + ",0.0," + rate + ",'',false");
        log("project", "add", "project: " + project + ", tenant: " + tenant
                + ", balance: " + balance + ", credit: " + credit);
        return new StatusMessage();
    }
}

class DisableProject extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(true, true)) {
            return insufficientPermissions;
        }

        if (!ns.getBoolean("y") && !confirmation()) {
            return new StatusMessage("failed to disable: no confirmation");
        }

        String project = ns.getString("project");
        ResultSet rs = select("project", "project='" + project + "'");
        if (!rs.next()) {
            return new StatusMessage("project does not exist");
        }
        if (rs.getBoolean("d")) {
            return new StatusMessage("project is already disabled");
        }
        if (rs.getFloat("requested") != 0) {
            return new StatusMessage("project cannot be disabled: pending transaction");
        }

        update("project", "d=true", "project='" + project + "'");
        log("project", "disable", "project: " + project);
        return new StatusMessage();
    }
}

class MovebudgetProject extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(true, true)) {
            return insufficientPermissions;
        }

        String type = ns.getString("type");
        String[] types = type.split("2");

        String from = ns.getString("from");
        String to = ns.getString("to");
        float balance = ns.getFloat("balance");
        float credit = ns.getFloat("credit");

        ResultSet fromRS, toRS;
        if (types[0].equals("p")) {
            fromRS = select("project", "project='" + from + "'");
            if (!fromRS.next()) {
                return new StatusMessage("from-project does not exist");
            }
            if (fromRS.getBoolean("d")) {
                return new StatusMessage("from-project is disabled");
            }
        } else {
            fromRS = select("tenant", "name='" + from + "'");
            if (!fromRS.next()) {
                return new StatusMessage("tenant does not exist");
            }
            if (fromRS.getBoolean("d")) {
                return new StatusMessage("tenant is disabled");
            }
        }
        if (types[1].equals("p")) {
            toRS = select("project", "project='" + to + "'");
            if (!toRS.next()) {
                return new StatusMessage("to-project does not exist");
            }
            if (toRS.getBoolean("d")) {
                return new StatusMessage("to-project is disabled");
            }
        } else {
            toRS = select("tenant", "name='" + to + "'");
            if (!toRS.next()) {
                return new StatusMessage("tenant does not exist");
            }
            if (toRS.getBoolean("d")) {
                return new StatusMessage("tenant is disabled");
            }
        }
        
        // ensure ownership (p belongs to t, both p are under same t)
        if (types[0].equals("p") && types[1].equals("p")) {
            if (!fromRS.getString("tenant").equalsIgnoreCase(toRS.getString("tenant"))) {
                return new StatusMessage("projects do not belong to the same tenant");
            }
        } else if (types[0].equals("p") && !fromRS.getString("tenant").equalsIgnoreCase(to)
                || types[1].equals("p") && !toRS.getString("tenant").equalsIgnoreCase(from)) {
            return new StatusMessage("project does not belong to tenant");
        }

        // if from tenant, check that this tenant has enough bal/cred
        if (types[0].equals("t")) {
            StatusMessage sm = sufficientBalCredit(from, fromRS.getFloat("balance"),
                    fromRS.getFloat("credit"), balance, credit);
            if (sm != null) {
                return sm;
            }
        } else {    // if from project, check the same, then update project bal
            float fromBalance = fromRS.getFloat("balance");
            float fromCredit = fromRS.getFloat("credit");
            if (fromBalance < balance) {
                return new StatusMessage("insufficient balance");
            }
            if (fromCredit < credit) {
                return new StatusMessage("insufficient credit");
            }
            update("project", "balance=" + (fromBalance - balance) + ",credit=" + (fromCredit - credit),
                    "project='" + from + "'");
        }

        // if there have been no errors, update only transfer is to a project (tenant doesn't need to be updated)
        if (types[1].equals("p")) {
            float toBalance = toRS.getFloat("balance");
            float toCredit = toRS.getFloat("credit");
            update("project", "balance=" + (toBalance + balance) + ",credit= " + (toCredit + credit),
                    "project='" + to + "'");
        }

        log("project", "muvebudget", "from: " + from + ", to: " + to + ", balance: " + balance
                + ", credit: " + credit + ", type: " + type);
        return new StatusMessage();
    }
}

class AddUser extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(true, true)) {
            return insufficientPermissions;
        }

        String project = ns.getString("project");
        ResultSet rs = select("project", "project='" + project + "'");
        if (!rs.next()) {
            return new StatusMessage("project does not exist");
        }
        if (rs.getBoolean("d")) {
            return new StatusMessage("project is disabled");
        }

        String user = ns.getString("user");
        ArrayList<String> users = fromCSV(rs.getString("users"));
        if (caseInsensitiveContains(users, user)) {
            return new StatusMessage("project already has this user");
        }
        if (!(user.length() <= 32 && isAlnum(user))) {
            return new StatusMessage("invalid user name");
        }

        users.add(user);
        update("project", "users='" + toCSV(users) + "'", "project='" + project +"'");
        log("user", "add", "project: " + project + ", user: " + user);
        return new StatusMessage();
    }
}

class DeleteUser extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(true, true)) {
            return insufficientPermissions;
        }

        String project = ns.getString("project");
        ResultSet rs = select("project", "project='" + project + "'");
        if (!rs.next()) {
            return new StatusMessage("project does not exist");
        }
        if (rs.getBoolean("d")) {
            return new StatusMessage("project is disabled");
        }

        String user = ns.getString("user");
        ArrayList<String> users = fromCSV(rs.getString("users"));
        if (!caseInsensitiveContains(users, user)) {
            return new StatusMessage("project does not have this user");
        }

        users.remove(user);
        update("project", "users='" + toCSV(users) + "'", "project='" + project + "'");
        log("user", "delete", "project: " + project + ", user: " + user);
        return new StatusMessage();
    }
}

class SetRate extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(false, true)) {
            return insufficientPermissions;
        }

        float rate = ns.getFloat("rate");
        if (!isMoney(rate)) {
            return new StatusMessage("invalid rate");
        }

        update("rate", "rate=" + rate);
        update("project", "rate=" + rate);
        log("rate", "set", "rate: " + rate);
        return new StatusMessage();
    }
}

class GetRate extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(false, true)) {
            return insufficientPermissions;
        }

        ResultSet rs = select("rate");
        if (!rs.next()) {
            return new StatusMessage("rate is improperly configured");
        }
        float rate = rs.getFloat("rate");
        return new StatusMessage(Json.createObjectBuilder().add("rate", rate));
    }
}

class ListCommand extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(true, true)) {
            return insufficientPermissions;
        }

        // these strings will be null if argument is unspecified
        String tenant = ns.getString("tenant");
        String project = ns.getString("project");
        String user = ns.getString("user");

        if (project != null) {
            ResultSet projectRS = select("project", "project='" + project + "'");
            if (!projectRS.next()) {
                return new StatusMessage("project not found");
            }
            if (projectRS.getBoolean("d")) {
                return new StatusMessage("project is disabled");
            }
            String projectTenant = projectRS.getString("tenant");
            if (tenant != null && !tenant.equalsIgnoreCase(projectTenant)) {
                return new StatusMessage("project does not belong to this tenant");
            }
            ArrayList<String> users = fromCSV(projectRS.getString("users"));
            if (user != null) {
                if (!caseInsensitiveContains(users, user)) {
                    return new StatusMessage("project does not have this user");
                }
            }

            ResultSet tenantRS = select("tenant", "name='" + projectTenant + "'");
            tenantRS.next();
            JsonArrayBuilder tenantsBuilder = Json.createArrayBuilder()
                    .add(tenantBuilder(tenantRS, Json.createArrayBuilder()
                            .add(projectBuilder(projectRS, users))));

            return new StatusMessage(Json.createObjectBuilder()
                    .add("list", tenantsBuilder));
        }

        ResultSet tenantRS = select("tenant", "d=false" + (tenant != null ? " AND name='" + tenant + "'" : ""));
        if (tenant != null) {
            if (!tenantRS.next()) {       // if tenant was not specified, then it being empty is fine
                return new StatusMessage("tenant does not exist");
            }
            if (tenantRS.getBoolean("d")) {
                return new StatusMessage("tenant is disabled");
            }
        }

        tenantRS.beforeFirst();
        boolean userFound = false;
        JsonArrayBuilder tenantBuilder = Json.createArrayBuilder();
        while (tenantRS.next()) {
            String tenantName = tenantRS.getString("name");
            ResultSet projectRS = select("project", "d=false AND tenant='" + tenantName + "'");

            JsonArrayBuilder projectBuilder = Json.createArrayBuilder();
            while (projectRS.next()) {
                ArrayList<String> users = fromCSV(projectRS.getString("users"));
                if (user != null) {
                    if (caseInsensitiveContains(users, user)) {
                        userFound = true;
                    } else {
                        continue;
                    }
                }
                projectBuilder.add(projectBuilder(projectRS, users));
            }
            tenantBuilder.add(tenantBuilder(tenantRS, projectBuilder));
        }

        if (user != null && !userFound) {
            return new StatusMessage("no such user found" + (tenant != null ? " for specified tenant" : ""));
        }

        return new StatusMessage(Json.createObjectBuilder()
                .add("list", tenantBuilder));
    }
}

class ReservebudgetTransaction extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;

        String project = ns.getString("project");
        ResultSet rs = select("project", "project='" + project + "'");
        if (!rs.next()) {
            return new StatusMessage("project does not exist");
        }
        if (rs.getBoolean("d")) {
            return new StatusMessage("project is disabled");
        }
        if (!verify(rs)) {
            return insufficientPermissions;
        }

        int estimate = ns.getInt("estimate");
        if (!isTime(estimate)) {
            return new StatusMessage("invalid estimate");
        }

        float requested = rs.getFloat("requested");
        float cost = rs.getFloat("rate") * estimate / 3600; // rate is in hours, estimate is in seconds
        if (rs.getFloat("balance") + rs.getFloat("credit") - requested < cost) {
            return new StatusMessage("insufficient project budget");
        }

        update("project", "requested=" + (requested + cost), "project='" + project + "'");
        return new StatusMessage();
    }
}

class ChargeTransaction extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;

        String project = ns.getString("project");
        ResultSet rs = select("project", "project='" + project + "'");
        if (!rs.next()) {
            return new StatusMessage("project does not exist");
        }
        if (rs.getBoolean("d")) {
            return new StatusMessage("project is disabled");
        }
        if (!verify(rs)) {
            return insufficientPermissions;
        }

        int estimate = ns.getInt("estimate");
        int jobtime = ns.getInt("jobtime");
        String start = ns.getString("start");
        if (!isTime(estimate)) {
            return new StatusMessage("invalid estimate");
        }
        if (!isTime(jobtime)) {
            return new StatusMessage("invalid jobtime");
        }
        if (!isDateTime(start)) {
            return new StatusMessage("invalid start time");
        }

        String user = System.getProperty("user.name");
        ArrayList<String> users = fromCSV(rs.getString("users"));
        if (!caseInsensitiveContains(users, user)) {
            return new StatusMessage("project does not contain this user");
        }

        float rate = rs.getFloat("rate");
        float balance = rs.getFloat("balance");
        float credit = rs.getFloat("credit");
        float currentRequested = rs.getFloat("requested");

        if (estimate > currentRequested) {
            return new StatusMessage("less than the estimate has been requested for this project");
        }

        float cost = rate * jobtime / 3600;
        float requested = rate * estimate / 3600;
        float newProjectBal, newProjectCredit;
        if (cost <= balance) {
            newProjectBal = balance - cost;
            newProjectCredit = credit;
        } else if (cost <= balance + credit) {
            newProjectBal = 0;
            newProjectCredit = credit - (cost - balance);
        } else {
            newProjectBal = balance - (cost - credit);
            newProjectCredit = 0;
        }

        String tenant = rs.getString("tenant");
        rs = select("tenant", "name='" + tenant + "'");
        rs.next();

        balance = rs.getFloat("balance");
        credit = rs.getFloat("credit");
        float newTenantBal, newTenantCredit;
        if (cost <= balance) {
            newTenantBal = balance - cost;
            newTenantCredit = credit;
        } else if (cost <= balance + credit) {
            newTenantBal = 0;
            newTenantCredit = credit - (cost - balance);
        } else {
            newTenantBal = balance - (cost - credit);
            newTenantCredit = 0;
        }

        LocalDateTime startDate = toDateTime(start);
        update("project", "requested=" + (currentRequested - requested) + ",balance=" + newProjectBal
                        + ",credit=" + newProjectCredit, "project='" + project + "'");
        update("tenant", "balance=" + newTenantBal + ",credit=" + newTenantCredit,
                "name='" + tenant + "'");
        insert("transaction", "project,user,start,end,runtime,cost", "'" + project + "','" + user
                + "','" + startDate.format(format) + "','" + startDate.plusSeconds(jobtime).format(format) + "',"
                + jobtime + "," + cost);
        return new StatusMessage();
    }
}

class GenerateBill extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(true, true)) {
            return insufficientPermissions;
        }

        String project = ns.getString("project");
        ResultSet projectRS = select("project", "project='" + project + "'");
        if (!projectRS.next()) {
            return new StatusMessage("project does not exist");
        }

        LocalDateTime now = now();
        LocalDateTime start, end;

        String timePeriod = ns.getString("timePeriod");
        String[] dates = timePeriod.split(",");
        if (dates.length == 2) {
            if (!isDate(dates[0]) || !isDate(dates[1])) {
                return new StatusMessage("invalid date format");
            }
            start = toDate(dates[0]);
            end = toDate(dates[1]);
        } else if (timePeriod.equalsIgnoreCase("last_day")) {
            start = now.minusDays(1);
            end = now;
        } else if (timePeriod.equalsIgnoreCase("last_week")) {
            start = now.minusDays(7);
            end = now;
        } else if (timePeriod.equalsIgnoreCase("last_month")) {
            start = now.minusDays(30);
            end = now;
        } else {
            return new StatusMessage("invalid date");
        }

        String tenant = projectRS.getString("tenant");
        ResultSet tenantRS = select("tenant", "name='" + tenant + "'");
        ResultSet transactionRS = select("transaction", "project='" + project + "' AND end>='"
                + start.format(format) + "'");
        ResultSet paymentRS = select("payment", "tenant='" + tenant + "' AND date>='"
                + start.format(format) + "'");

        tenantRS.next();
        float balance = tenantRS.getFloat("balance");

        // sum of transactions/payments after the date range specified
        HashSet<String> uniqueDates = new HashSet<>();
        float rangeTransactionTotal = 0, rangePaymentTotal = 0;
        // sum of transactions/payments after the date range specified (but before today)
        float postTransactionTotal = 0, postPaymentTotal = 0;

        while (transactionRS.next()) {
            LocalDateTime transactionEnd = toDateTime(transactionRS.getTimestamp("end"));
            if (transactionEnd.isAfter(end)) {
                postTransactionTotal += transactionRS.getFloat("cost");
            } else {
                uniqueDates.add(transactionEnd.format(billFormat));
                rangeTransactionTotal += transactionRS.getFloat("cost");
            }
        }
        while (paymentRS.next()) {
            if (toDateTime(paymentRS.getTimestamp("date")).isAfter(end)) {
                postPaymentTotal += paymentRS.getFloat("payment");
            } else {
                rangePaymentTotal += paymentRS.getFloat("payment");
            }
        }

        float endingBal = balance - postPaymentTotal + postTransactionTotal;
        float startingBal = endingBal - rangePaymentTotal + rangeTransactionTotal;

        HashMap<String, HashMap<String, Float>> bill = new HashMap<>();

        for (String date : uniqueDates) {
            bill.put(date, new HashMap<>());
        }

        float totalCost = 0f, totalHours = 0f;
        transactionRS.beforeFirst();        // allows us to loop through result set twice
        while (transactionRS.next()) {
            LocalDateTime transactionEnd = toDateTime(transactionRS.getTimestamp("end"));
            if (transactionEnd.isBefore(end)) {
                float runtime = transactionRS.getFloat("runtime") / 3600;
                totalHours += runtime;
                totalCost += transactionRS.getFloat("cost");

                String user = transactionRS.getString("user");
                HashMap<String, Float> activities = bill.get(transactionEnd.format(billFormat));
                if (activities.containsKey(user)) {
                    activities.put(user, activities.get(user) + runtime);
                } else {
                    activities.put(user, runtime);
                }
            }
        }

        // converting bill to json
        JsonArrayBuilder billBuilder = Json.createArrayBuilder();
        for (String date : bill.keySet()) {
            HashMap<String, Float> activities = bill.get(date);
            JsonArrayBuilder activitiesBuilder = Json.createArrayBuilder();
            for (String user : activities.keySet()) {
                activitiesBuilder.add(Json.createObjectBuilder()
                        .add("user", user)
                        .add("hours", round(activities.get(user))));        // rounding values
            }
            billBuilder.add(Json.createObjectBuilder()
                    .add("date", date)
                    .add("activity", activitiesBuilder));
        }

        return new StatusMessage(Json.createObjectBuilder()
                .add("bill", Json.createObjectBuilder()
                        .add("tenant", tenant)
                        .add("project", project)
                        .add("from", start.format(format))
                        .add("to", end.format(format))
                        .add("bill", billBuilder)
                        .add("total_hours", round(totalHours))
                        .add("total_cost", round(totalCost))
                        .add("bbalance", round(startingBal))
                        .add("payments", round(rangePaymentTotal))
                        .add("ebalance", round(endingBal))));
    }
}

class AddAdmin extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verifyRoot()) {
            return insufficientPermissions;
        }

        String user = ns.getString("user");
        ResultSet rs = select("role", "name='" + user + "'");
        if (!rs.next()) {
            insert("role", "name,tenantadmin,admin", "'" + user + "',false,true");
        } else if (rs.getBoolean("admin")) {
            return new StatusMessage("user is already an admin");
        } else {
            update("role", "admin=true", "name='" + user + "'");
        }
        log("role", "add", "role: admin, name: " + user);
        return new StatusMessage();
    }
}

class AddTenantadmin extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(false, true)) {
            return insufficientPermissions;
        }

        String user = ns.getString("user");
        ResultSet rs = select("role", "name='" + user + "'");
        if (!rs.next()) {
            insert("role", "name,tenantadmin,admin", "'" + user + "',true,false");
        } else if (rs.getBoolean("admin")) {
            return new StatusMessage("user is already a tenantadmin");
        } else {
            update("role", "tenantadmin=true", "name='" + user + "'");
        }
        log("role", "add", "role: tenantadmin, name: " + user);
        return new StatusMessage();
    }
}

class DeleteAdmin extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verifyRoot()) {
            return insufficientPermissions;
        }

        String user = ns.getString("user");
        ResultSet rs = select("role", "name='" + user + "'");
        if (!rs.next() || !rs.getBoolean("admin")) {
            return new StatusMessage("user is not an admin");
        }
        update("role", "admin=false", "name='" + user + "'");
        log("role", "delete", "role: admin, name: " + user);
        return new StatusMessage();
    }
}

class DeleteTenantadmin extends Command {
    @Override
    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
        this.c = c;
        if (!verify(false, true)) {
            return insufficientPermissions;
        }

        String user = ns.getString("user");
        ResultSet rs = select("role", "name='" + user + "'");
        if (!rs.next() || !rs.getBoolean("tenantadmin")) {
            return new StatusMessage("user is not a tenantadmin");
        }
        update("role", "tenantadmin=false", "name='" + user + "'");
        log("role", "delete", "role: tenantadmin, name: " + user);
        return new StatusMessage();
    }
}

//class Template extends Command {
//    @Override
//    StatusMessage execute(Namespace ns, Connection c) throws SQLException {
//        this.c = c;
//
//        return null;
//    }
//}

public class dca {
    private static Namespace parse(String[] args) {
        ArgumentParser parser = ArgumentParsers.newArgumentParser("dca")
                .defaultHelp(true);
        Subparsers subparsers = parser.addSubparsers();

        /* WIPE PARSER */
        Subparser wipeParser = subparsers.addParser("wipe").help("Wipe SQL tables.");
        wipeParser.setDefault("cmd", new WipeSQL());
        wipeParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* SETUP PARSER */
        Subparser setupParser = subparsers.addParser("setup").help("Set up dca - creates MySQL tables.");
        setupParser.setDefault("cmd", new SetupSQL());
        setupParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* TENANT PARSER */
        Subparser tenantParser = subparsers.addParser("tenant").help("Manipulate tenant data.");
        Subparsers tenantSubparsers = tenantParser.addSubparsers();

        Subparser addTenantParser = tenantSubparsers.addParser("add").help("Add a new tenant.");
        addTenantParser.setDefault("cmd", new AddTenant());
        addTenantParser.addArgument("-t", "--tenant").help("Tenant name.")
                .type(String.class)
                .metavar("TENANT")
                .required(true);
        addTenantParser.addArgument("-c", "--credit").help("Initial credit.")
                .type(Float.class)
                .metavar("CREDIT")
                .setDefault(0f);
        addTenantParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser disableTenantParser = tenantSubparsers.addParser("disable").help("Disable an existing tenant.");
        disableTenantParser.setDefault("cmd", new DisableTenant());
        disableTenantParser.addArgument("-t", "--tenant").help("Tenant name.")
                .type(String.class)
                .metavar("TENANT")
                .required(true);
        disableTenantParser.addArgument("-y").help("Skips confirmation message.")
                .action(storeTrue());
        disableTenantParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser modifyTenantParser = tenantSubparsers.addParser("modify").help("Modify an existing tenant.");
        modifyTenantParser.setDefault("cmd", new ModifyTenant());
        modifyTenantParser.addArgument("-t", "--tenant").help("Tenant name.")
                .type(String.class)
                .metavar("TENANT")
                .required(true);
        modifyTenantParser.addArgument("-c", "--credit").help("Credit added.")
                .type(Float.class)
                .metavar("CREDIT")
                .required(true);
        modifyTenantParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser paymentTenantParser = tenantSubparsers.addParser("payment").help("Make a payment to a tenant.");
        paymentTenantParser.setDefault("cmd", new PaymentTenant());
        paymentTenantParser.addArgument("-t", "--tenant").help("Tenant name.")
                .type(String.class)
                .metavar("TENANT")
                .required(true);
        paymentTenantParser.addArgument("-p", "--payment").help("Payment amount.")
                .type(Float.class)
                .metavar("PAYMENT")
                .required(true);
        paymentTenantParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* PROJECT PARSER */
        Subparser projectParser = subparsers.addParser("project").help("Manipulate project data.");
        Subparsers projectSubparsers = projectParser.addSubparsers();

        Subparser addProjectParser = projectSubparsers.addParser("add").help("Add a new project");
        addProjectParser.setDefault("cmd", new AddProject());
        addProjectParser.addArgument("-t", "--tenant").help("Tenant name.")
                .type(String.class)
                .metavar("TENANT")
                .required(true);
        addProjectParser.addArgument("-p", "--project").help("Project name.")
                .type(String.class)
                .metavar("PROJECT")
                .required(true);
        addProjectParser.addArgument("-b", "--balance").help("Balance allocated from tenant to project.")
                .type(Float.class)
                .metavar("BALANCE")
                .setDefault(0f);
        addProjectParser.addArgument("-c", "--credit").help("Credit allocated from tenant to project.")
                .type(Float.class)
                .metavar("CREDIT")
                .setDefault(0f);
        addProjectParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser disableProjectParser = projectSubparsers.addParser("disable").help("Disable an existing project.");
        disableProjectParser.setDefault("cmd", new DisableProject());
        disableProjectParser.addArgument("-p", "--project").help("Project name.")
                .type(String.class)
                .metavar("PROJECT")
                .required(true);
        disableProjectParser.addArgument("-y").help("Skips confirmation message.")
                .action(storeTrue());
        disableProjectParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser movebudgetProjectParser = projectSubparsers.addParser("movebudget")
                .help("Move budget from one source to another.");
        movebudgetProjectParser.setDefault("cmd", new MovebudgetProject());
        movebudgetProjectParser.addArgument("--from")
                .help("Account to move budget from. Can be a tenant or a project.")
                .type(String.class)
                .metavar("FROM")
                .required(true);
        movebudgetProjectParser.addArgument("--to")
                .help("Account to move budget to. Can be a tenant or a project.")
                .type(String.class)
                .metavar("TO")
                .required(true);
        movebudgetProjectParser.addArgument("-b", "--balance").help("Balance transferred.")
                .type(Float.class)
                .metavar("BALANCE")
                .setDefault(0f);
        movebudgetProjectParser.addArgument("-c", "--credit").help("Credit transferred.")
                .type(Float.class)
                .metavar("CREDIT")
                .setDefault(0f);
        movebudgetProjectParser.addArgument("-t", "--type").help("Type of transfer: p2p, t2p, or p2t")
                .choices("p2p", "t2p", "p2t")
                .required(true);
        movebudgetProjectParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* USER PARSER */
        Subparser userParser = subparsers.addParser("user").help("Manipulate user data.");
        Subparsers userSubparsers = userParser.addSubparsers();

        Subparser addUserParser = userSubparsers.addParser("add").help("Add a new user.");
        addUserParser.setDefault("cmd", new AddUser());
        addUserParser.addArgument("-p", "--project")
                .type(String.class)
                .metavar("PROJECT")
                .required(true);
        addUserParser.addArgument("-u", "--user")
                .type(String.class)
                .metavar("USER")
                .required(true);
        addUserParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser deleteUserParser = userSubparsers.addParser("delete").help("Delete an existing user.");
        deleteUserParser.setDefault("cmd", new DeleteUser());
        deleteUserParser.addArgument("-p", "--project")
                .type(String.class)
                .metavar("PROJECT")
                .required(true);
        deleteUserParser.addArgument("-u", "--user")
                .type(String.class)
                .metavar("USER")
                .required(true);
        deleteUserParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* LIST PARSER */
        Subparser listParser = subparsers.addParser("list")
                .help("List billing information about a specific tenant, project, user, or any combination of the three.");
        listParser.setDefault("cmd", new ListCommand());
        listParser.addArgument("-t", "--tenant").help("Tenant name.")
                .type(String.class)
                .metavar("TENANT");
        listParser.addArgument("-p", "--project")
                .type(String.class)
                .metavar("PROJECT");
        listParser.addArgument("-u", "--user")
                .type(String.class)
                .metavar("USER");
        listParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* RATE PARSER */
        Subparser rateParser = subparsers.addParser("rate").help("Setting and getting information about the rate.");
        Subparsers rateSubparsers = rateParser.addSubparsers();

        Subparser setRateParser = rateSubparsers.addParser("set").help("Set rate.");
        setRateParser.setDefault("cmd", new SetRate());
        setRateParser.addArgument("-r", "--rate").help("New rate.")
                .type(Float.class)
                .metavar("RATE")
                .required(true);
        setRateParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser getRateParser = rateSubparsers.addParser("get").help("Get rate.");
        getRateParser.setDefault("cmd", new GetRate());
        getRateParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* TRANSACTION PARSER */
        Subparser transactionParser = subparsers.addParser("transaction")
                .help("Reserving and charging project budgets.");
        Subparsers transactionSubparsers = transactionParser.addSubparsers();

        Subparser reservebudgetTransactionParser = transactionSubparsers.addParser("reservebudget")
                .help("Reserve a project's budget.");
        reservebudgetTransactionParser.setDefault("cmd", new ReservebudgetTransaction());
        reservebudgetTransactionParser.addArgument("-p", "--project").help("Project name.")
                .type(String.class)
                .metavar("PROJECT")
                .required(true);
        reservebudgetTransactionParser.addArgument("-e", "--estimate").help("Estimate for processing time required.")
                .type(Integer.class)
                .metavar("ESTIMATE")
                .required(true);
        reservebudgetTransactionParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser chargeTransactionParser = transactionSubparsers.addParser("charge")
                .help("Charges a user and its project.");
        chargeTransactionParser.setDefault("cmd", new ChargeTransaction());
        chargeTransactionParser.addArgument("-p", "--project")
                .type(String.class)
                .metavar("PROJECT")
                .required(true);
        chargeTransactionParser.addArgument("-e", "--estimate")
                .type(Integer.class)
                .metavar("ESTIMATE")
                .required(true);
        chargeTransactionParser.addArgument("-j", "--jobtime")
                .type(Integer.class)
                .metavar("TIME")
                .required(true);
        chargeTransactionParser.addArgument("-s", "--start")
                .type(String.class)
                .metavar("START")
                .required(true);
        chargeTransactionParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* BILL PARSER */
        Subparser billParser = subparsers.addParser("bill").help("Bill related functions.");
        Subparsers billSubparsers = billParser.addSubparsers();

        Subparser generateBillParser = billSubparsers.addParser("generate").help("Generating bills.");
        generateBillParser.setDefault("cmd", new GenerateBill());
        generateBillParser.addArgument("-p", "--project")
                .type(String.class)
                .metavar("PROJECT")
                .required(true);
        generateBillParser.addArgument("--time_period")
                .dest("timePeriod")
                .type(String.class)
                .metavar("PERIOD")
                .required(true);
        generateBillParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        /* ROLE PARSER */
        Subparser roleParser = subparsers.addParser("role").help("Add/remove users from roles.");
        Subparsers roleParsers = roleParser.addSubparsers();

        Subparser addRoleParser = roleParsers.addParser("add").help("Add a user to a role.");
        Subparsers addRoleSubparsers = addRoleParser.addSubparsers();

        Subparser addAdminParser = addRoleSubparsers.addParser("admin").help("Give a user admin privileges.");
        addAdminParser.setDefault("cmd", new AddAdmin());
        addAdminParser.addArgument("-u", "--user")
                .type(String.class)
                .metavar("USER")
                .required(true);
        addAdminParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser addTenantadminParser = addRoleSubparsers.addParser("tenantadmin")
                .help("Give a user tenantadmin privileges");
        addTenantadminParser.setDefault("cmd", new AddTenantadmin());
        addTenantadminParser.addArgument("-u", "--user")
                .type(String.class)
                .metavar("USER")
                .required(true);
        addTenantadminParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser deleteRoleParser = roleParsers.addParser("delete").help("Delete a role from a user.");
        Subparsers deleteRoleSubparsers = deleteRoleParser.addSubparsers();

        Subparser deleteAdminParser = deleteRoleSubparsers.addParser("admin").help("Removes admin privileges from a user.");
        deleteAdminParser.setDefault("cmd", new DeleteAdmin());
        deleteAdminParser.addArgument("-u", "--user")
                .type(String.class)
                .metavar("USER")
                .required(true);
        deleteAdminParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        Subparser deleteTenantadminParser = deleteRoleSubparsers.addParser("tenantadmin")
                .help("Removes tenantadmin privileges from a user.");
        deleteTenantadminParser.setDefault("cmd", new DeleteTenantadmin());
        deleteTenantadminParser.addArgument("-u", "--user")
                .type(String.class)
                .metavar("USER")
                .required(true);
        deleteTenantadminParser.addArgument("-m", "--mini").help("Mini-print (no newlines or tabs) output.")
                .action(storeTrue());

        if (args.length == 0) {
            parser.printHelp();
            System.exit(1);
        }
        return parser.parseArgsOrFail(args);
    }

    private static Connection initSQL() {
        try {
            Class.forName("com.mysql.jdbc.Driver");
            return DriverManager.getConnection("jdbc:mysql://localhost:3306/dca",
                    "root", "password");
        } catch(SQLException e) {
            System.out.println("Unable to connect to MySQL Server.");
            System.exit(1);
        } catch(ClassNotFoundException e) {
            System.out.println("You do not have a suitable JDBC driver.");
            System.exit(1);
        }
        return null;
    }

    public static void main(String[] args) {
        Namespace ns = parse(args);
        try {
            Command cmd = ns.get("cmd");
            StatusMessage sm = cmd.execute(ns, initSQL());
            if (ns.getBoolean("mini")) {
                sm.print();
            } else {
                sm.pprint();
            }
        } catch(SQLException e) {
            e.printStackTrace();
        }
    }
}

/*
    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "taskfactory.h"
#include <algorithm>
#include "common/camcopsapp.h"
#include "tasklib/task.h"
#include "tasklib/tasksorter.h"


// ===========================================================================
// TaskFactory
// ===========================================================================

TaskFactory::TaskFactory(CamcopsApp& app) :
    m_app(app)
{
}


void TaskFactory::registerTask(ProxyType proxy)
{
    m_initial_proxy_list.append(proxy);
    // We are here from WITHIN A CONSTRUCTOR (TaskProxy::TaskProxy), so don't
    // call back to the proxy.
}


void TaskFactory::finishRegistration()
{
    for (int i = 0; i < m_initial_proxy_list.size(); ++i) {
        ProxyType proxy = m_initial_proxy_list[i];
        TaskPtr p_task = proxy->create(m_app, m_app.db());
        TaskCache cache;
        cache.tablename = p_task->tablename();
        cache.shortname = p_task->shortname();
        cache.longname = p_task->longname();
        cache.proxy = proxy;
        if (m_map.contains(cache.tablename)) {
            QString msg = QString(
                "BAD TASK REGISTRATION: table %1 being registered for a second"
                " time by task with longname %2").arg(
                    cache.tablename, cache.longname);
            qFatal("%s", qPrintable(msg));
        }
        m_map.insert(cache.tablename, cache);  // tablenames are the keys
        m_tablenames.append(cache.tablename);
    }
    m_tablenames.sort();
}


QStringList TaskFactory::tablenames() const
{
    return m_tablenames;
}


TaskPtr TaskFactory::create(const QString& key, int load_pk) const
{
    if (!m_map.contains(key)) {
        qWarning().nospace() << "TaskFactory::create(" << key << ", "
                             << load_pk << ")" << "... no such task class";
        return TaskPtr(nullptr);
    }
    qDebug().nospace() << "TaskFactory::create(" << key << ", "
                       << load_pk << ")";
    ProxyType proxy = m_map[key].proxy;
    return proxy->create(m_app, m_app.db(), load_pk);
}


void TaskFactory::makeAllTables() const
{
    MapIteratorType it(m_map);
    while (it.hasNext()) {
        it.next();
        ProxyType proxy = it.value().proxy;
        TaskPtr p_task = proxy->create(m_app, m_app.db());
        p_task->makeTables();
    }
}


QString TaskFactory::shortname(const QString& key) const
{
    if (!m_map.contains(key)) {
        qWarning() << "Bad task: " << key;
        return nullptr;
    }
    return m_map[key].shortname;
}


QString TaskFactory::longname(const QString& key) const
{
    if (!m_map.contains(key)) {
        qWarning() << "Bad task: " << key;
        return nullptr;
    }
    return m_map[key].longname;
}


void TaskFactory::makeTables(const QString& key) const
{
    TaskPtr p_task = create(key);
    if (!p_task) {
        return;
    }
    p_task->makeTables();
}


TaskPtrList TaskFactory::fetch(const QString& tablename, bool sort) const
{
    // KEY SECURITY DECISIONS IMPLEMENTED HERE: which tasks users can see.
    int patient_id = m_app.selectedPatientId();
    bool patient_selected = patient_id != DbConst::NONEXISTENT_PK;
    TaskPtrList tasklist;
    if (tablename.isEmpty()) {
        // Patient summary view; "all tasks" request.
        // - Patient selected -> all tasks for current patient (whether locked
        //   or not).
        // - No patient selected -> return nothing.
        if (patient_selected) {
            MapIteratorType it(m_map);
            while (it.hasNext()) {
                it.next();
                ProxyType proxy = it.value().proxy;
                tasklist += proxy->fetch(m_app, m_app.db(), patient_id);
            }
        }
    } else if (!m_map.contains(tablename)) {
        // Duff task
        qWarning() << "Bad task: " << tablename;
    } else {
        // Specific task
        // - Patient-based task / patient selected -> tasks for that patient
        //   (whether locked or not).
        // - Patient-based task / no patient selected / unlocked -> all such
        //   tasks, for all patients.
        // - Patient-based task / no patient selected / locked -> nothing.
        // - Anonymous task / patient selected -> all such tasks
        //   ... see also TaskRegistrar::fetch().
        //   ... if you choose "none", users will probably wonder where
        //       tasks are vanishing to
        // - Anonymous task / no patient selected -> all such tasks
        ProxyType proxy = m_map[tablename].proxy;
        TaskPtr specimen = proxy->create(m_app, m_app.db(),
                                         DbConst::NONEXISTENT_PK);
        bool anonymous = specimen->isAnonymous();
        bool locked = m_app.locked();
        if (anonymous) {
            tasklist = proxy->fetch(m_app, m_app.db(), DbConst::NONEXISTENT_PK);
        } else {
            if (patient_selected || !locked) {
                tasklist = proxy->fetch(m_app, m_app.db(), patient_id);
            }
        }
    }

    if (sort) {
        qDebug() << "Starting sort...";
        qSort(tasklist.begin(), tasklist.end(), TaskSorter());
        qDebug() << "... finished sort";
    }

    return tasklist;
}

## current_session_filters.mako
<%page args="task_filter: TaskFilter"/>

<%!

from markupsafe import escape
from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_dt import format_datetime

%>

<%
    some_filter = False
%>

<div class="filters">
    ## Task types
    %if task_filter.task_types:
        Task is one of: <b>${ ", ".join(task_filter.task_types) }</b>.
        <% some_filter = True %>
    %endif
    ## Patient
    %if task_filter.surname:
        Surname = <b>${ task_filter.surname | h }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.forename:
        Forename = <b>${ task_filter.forename | h }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.dob:
        DOB = <b>${ format_datetime(task_filter.dob, DateFormat.SHORT_DATE) }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.sex:
        Sex = <b>${ task_filter.sex }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.idnum_criteria:
        ID numbers match one of:
        ${ ("; ".join("{which} = <b>{value}</b>".format(
                which=request.get_id_shortdesc(iddef.which_idnum),
                value=iddef.idnum_value,
            ) for iddef in task_filter.idnum_criteria) + ".") }
        <% some_filter = True %>
    %endif
    ## Other
    %if task_filter.device_ids:
        Uploading device is one of: <b>${ ", ".join(escape(d) for d in task_filter.get_device_names(request)) }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.adding_user_ids:
        Adding user is one of: <b>${ ", ".join(escape(u) for u in task_filter.get_user_names(request)) }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.group_ids:
        Group is one of: <b>${ ", ".join(escape(g) for g in task_filter.get_group_names(request)) }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.start_datetime:
        Created <b>&ge; ${ task_filter.start_datetime }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.end_datetime:
        Created <b>&le; ${ task_filter.end_datetime }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.text_contents:
        Text contains one of: <b>${ ", ".join(escape(repr(t)) for t in task_filter.text_contents) }</b>.
        <% some_filter = True %>
    %endif
    %if task_filter.complete_only:
        <b>Restricted to “complete” tasks only.</b>
        <% some_filter = True %>
    %endif

    %if not some_filter:
        [No filters.]
    %endif
</div>

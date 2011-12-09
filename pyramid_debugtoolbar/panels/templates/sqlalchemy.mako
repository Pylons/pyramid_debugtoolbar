<table id="pSqlaTable">
	<thead>
		<tr>
			<th>Time&nbsp;(ms)</th>
			<th>Action</th>
			<th>Query</th>
			<th>Params</th>
		</tr>
	</thead>
	<tbody>
	% for i, query in enumerate(queries):
		<tr class="${i%2 and 'pDebugEven' or 'pDebugOdd'}">
			<td>${'%.4f' % query['duration']}</td>
			<td>
			% if query['params']:
				% if query['is_select']:
				<a class="remoteCall" href="${root_path}/sqlalchemy/sql_select?sql=${query['raw_sql']|u}&amp;params=${query['params']}&amp;duration=${str(query['duration'])|u}&amp;hash=${query['hash']}&amp;engine_id=${str(query['engine_id'])|u}">SELECT</a><br />
				<a class="remoteCall" href="${root_path}/sqlalchemy/sql_explain?sql=${query['raw_sql']|u}&amp;params=${query['params']}&amp;duration=${str(query['duration'])|u}&amp;hash=${query['hash']}&amp;engine_id=${str(query['engine_id'])|u}">EXPLAIN</a><br />
				% endif
			% endif
			</td>
			<td>${query['sql']|n}</td>
			<td>${query['params']|n}</td>
		</tr>
	% endfor
	</tbody>
</table>

